// Thread Manager for tracking and managing all async operations, workers, and timers
// Helps prevent memory leaks, runaway operations, and assists with debugging

// Helper function to safely get current time
function getTime() {
  if (typeof performance !== 'undefined' && performance.now) {
    return performance.now();
  }
  return Date.now();
}

class ThreadManager {
  constructor() {
    this.operations = new Map();
    this.workers = new Map();
    this.timers = new Map();
    this.intervals = new Map();
    this.operationId = 0;
    this.performanceMetrics = new Map();
    this.debugMode = import.meta.env.MODE === 'development';
    this.maxOperationTime = 30000; // 30 seconds default max operation time
    this.warningThreshold = 5000; // Warn after 5 seconds
    
    // Bind cleanup to window events
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => this.cleanup());
      
      // Expose to window for debugging in development
      if (this.debugMode) {
        window.__threadManager = this;
      }
    }
  }

  // Register an async operation
  registerOperation(name, options = {}) {
    const id = ++this.operationId;
    let stackTrace = null;
    
    // Safely capture stack trace in debug mode
    if (this.debugMode) {
      try {
        const err = new Error();
        stackTrace = err.stack || null;
      } catch (e) {
        // Stack trace not available in this environment
        stackTrace = null;
      }
    }
    
    const operation = {
      id,
      name,
      type: options.type || 'async',
      startTime: getTime(),
      stackTrace,
      timeout: options.timeout || this.maxOperationTime,
      warningThreshold: options.warningThreshold || this.warningThreshold,
      metadata: options.metadata || {},
      status: 'running',
      promise: null,
      cancelFn: options.cancelFn || null,
      parentOperation: options.parentOperation || null
    };

    this.operations.set(id, operation);

    // Set up timeout handler
    const timeoutId = setTimeout(() => {
      this.handleOperationTimeout(id);
    }, operation.timeout);

    operation.timeoutId = timeoutId;

    // Set up warning handler
    if (operation.warningThreshold) {
      const warningId = setTimeout(() => {
        this.handleOperationWarning(id);
      }, operation.warningThreshold);
      operation.warningId = warningId;
    }

    if (this.debugMode) {
      console.log(`🧵 Thread Manager: Started operation "${name}" (ID: ${id})`);
    }

    return {
      id,
      complete: (result) => this.completeOperation(id, result),
      fail: (error) => this.failOperation(id, error),
      update: (metadata) => this.updateOperation(id, metadata)
    };
  }

  // Complete an operation
  completeOperation(id, result = null) {
    const operation = this.operations.get(id);
    if (!operation) return;

    const duration = getTime() - operation.startTime;
    operation.status = 'completed';
    operation.duration = duration;
    operation.result = result;
    operation.endTime = getTime();

    // Clear timeouts
    clearTimeout(operation.timeoutId);
    if (operation.warningId) clearTimeout(operation.warningId);

    // Record performance metrics
    this.recordMetrics(operation);

    if (this.debugMode && duration > 1000) {
      console.log(`🧵 Thread Manager: Completed operation "${operation.name}" (ID: ${id}) in ${duration.toFixed(2)}ms`);
    }

    // Clean up after a delay to allow for debugging
    setTimeout(() => {
      this.operations.delete(id);
    }, this.debugMode ? 60000 : 5000); // Keep for 1 minute in debug, 5 seconds in production
  }

  // Fail an operation
  failOperation(id, error) {
    const operation = this.operations.get(id);
    if (!operation) return;

    const duration = getTime() - operation.startTime;
    operation.status = 'failed';
    operation.duration = duration;
    operation.error = error;
    operation.endTime = getTime();

    // Clear timeouts
    clearTimeout(operation.timeoutId);
    if (operation.warningId) clearTimeout(operation.warningId);

    // Record performance metrics
    this.recordMetrics(operation);

    console.error(`🧵 Thread Manager: Operation "${operation.name}" (ID: ${id}) failed after ${duration.toFixed(2)}ms:`, error);
    
    if (this.debugMode && operation.stackTrace) {
      console.error('Stack trace:', operation.stackTrace);
    }

    // Clean up after a delay
    setTimeout(() => {
      this.operations.delete(id);
    }, this.debugMode ? 60000 : 5000);
  }

  // Update operation metadata
  updateOperation(id, metadata) {
    const operation = this.operations.get(id);
    if (operation) {
      operation.metadata = { ...operation.metadata, ...metadata };
    }
  }

  // Handle operation timeout
  handleOperationTimeout(id) {
    const operation = this.operations.get(id);
    if (!operation || operation.status !== 'running') return;

    console.error(`🧵 Thread Manager: Operation "${operation.name}" (ID: ${id}) timed out after ${operation.timeout}ms`);
    
    if (operation.stackTrace) {
      console.error('Stack trace:', operation.stackTrace);
    }

    // Try to cancel the operation if possible
    if (operation.cancelFn) {
      try {
        operation.cancelFn();
        console.log(`🧵 Thread Manager: Attempted to cancel operation "${operation.name}"`);
      } catch (error) {
        console.error('Failed to cancel operation:', error);
      }
    }

    operation.status = 'timeout';
    operation.endTime = getTime();
    
    // Record metrics
    this.recordMetrics(operation);
  }

  // Handle operation warning
  handleOperationWarning(id) {
    const operation = this.operations.get(id);
    if (!operation || operation.status !== 'running') return;

    const duration = getTime() - operation.startTime;
    console.warn(`🧵 Thread Manager: Operation "${operation.name}" (ID: ${id}) has been running for ${duration.toFixed(2)}ms`);
    
    if (this.debugMode && operation.metadata) {
      console.warn('Operation metadata:', operation.metadata);
    }
  }

  // Register a Web Worker
  registerWorker(name, worker) {
    const id = `worker_${++this.operationId}`;
    this.workers.set(id, {
      id,
      name,
      worker,
      startTime: getTime(),
      status: 'active'
    });

    if (this.debugMode) {
      console.log(`🧵 Thread Manager: Registered worker "${name}" (ID: ${id})`);
    }

    return id;
  }

  // Unregister a Web Worker
  unregisterWorker(id) {
    const workerInfo = this.workers.get(id);
    if (workerInfo) {
      const duration = getTime() - workerInfo.startTime;
      if (this.debugMode) {
        console.log(`🧵 Thread Manager: Unregistered worker "${workerInfo.name}" (ID: ${id}) after ${duration.toFixed(2)}ms`);
      }
      this.workers.delete(id);
    }
  }

  // Register a timer
  registerTimer(name, timerId, type = 'timeout', delay = 0) {
    const id = `timer_${++this.operationId}`;
    const collection = type === 'interval' ? this.intervals : this.timers;
    
    collection.set(id, {
      id,
      name,
      timerId,
      type,
      delay,
      startTime: getTime()
    });

    return id;
  }

  // Unregister a timer
  unregisterTimer(id) {
    const timer = this.timers.get(id) || this.intervals.get(id);
    if (timer) {
      const duration = getTime() - timer.startTime;
      if (this.debugMode && duration > 1000) {
        console.log(`🧵 Thread Manager: Unregistered ${timer.type} "${timer.name}" (ID: ${id}) after ${duration.toFixed(2)}ms`);
      }
      this.timers.delete(id);
      this.intervals.delete(id);
    }
  }

  // Record performance metrics
  recordMetrics(operation) {
    const key = operation.name;
    const metrics = this.performanceMetrics.get(key) || {
      count: 0,
      totalDuration: 0,
      averageDuration: 0,
      maxDuration: 0,
      minDuration: Infinity,
      failures: 0,
      timeouts: 0
    };

    metrics.count++;
    metrics.totalDuration += operation.duration;
    metrics.averageDuration = metrics.totalDuration / metrics.count;
    metrics.maxDuration = Math.max(metrics.maxDuration, operation.duration);
    metrics.minDuration = Math.min(metrics.minDuration, operation.duration);

    if (operation.status === 'failed') metrics.failures++;
    if (operation.status === 'timeout') metrics.timeouts++;

    this.performanceMetrics.set(key, metrics);
  }

  // Get current status
  getStatus() {
    const runningOps = Array.from(this.operations.values())
      .filter(op => op.status === 'running')
      .map(op => ({
        id: op.id,
        name: op.name,
        duration: getTime() - op.startTime,
        metadata: op.metadata
      }));

    return {
      runningOperations: runningOps,
      activeWorkers: this.workers.size,
      activeTimers: this.timers.size,
      activeIntervals: this.intervals.size,
      performanceMetrics: Object.fromEntries(this.performanceMetrics)
    };
  }

  // Get problematic operations
  getProblematicOperations() {
    const threshold = 5000; // 5 seconds
    const now = getTime();
    
    return Array.from(this.operations.values())
      .filter(op => op.status === 'running' && (now - op.startTime) > threshold)
      .map(op => ({
        id: op.id,
        name: op.name,
        duration: now - op.startTime,
        stackTrace: op.stackTrace,
        metadata: op.metadata
      }));
  }

  // Force cleanup of long-running operations
  forceCleanup(threshold = 60000) {
    const now = getTime();
    let cleaned = 0;

    // Clean up operations
    for (const [id, operation] of this.operations) {
      if (operation.status === 'running' && (now - operation.startTime) > threshold) {
        console.warn(`🧵 Thread Manager: Force cleaning operation "${operation.name}" (ID: ${id})`);
        if (operation.cancelFn) {
          try {
            operation.cancelFn();
          } catch (error) {
            console.error('Failed to cancel operation:', error);
          }
        }
        this.failOperation(id, new Error('Force cleaned due to timeout'));
        cleaned++;
      }
    }

    // Terminate stuck workers
    for (const [id, workerInfo] of this.workers) {
      if ((now - workerInfo.startTime) > threshold) {
        console.warn(`🧵 Thread Manager: Terminating stuck worker "${workerInfo.name}" (ID: ${id})`);
        try {
          workerInfo.worker.terminate();
        } catch (error) {
          console.error('Failed to terminate worker:', error);
        }
        this.workers.delete(id);
        cleaned++;
      }
    }

    console.log(`🧵 Thread Manager: Force cleaned ${cleaned} operations/workers`);
    return cleaned;
  }

  // Generate debug report
  generateDebugReport() {
    const status = this.getStatus();
    const problematic = this.getProblematicOperations();
    
    return {
      timestamp: new Date().toISOString(),
      status,
      problematicOperations: problematic,
      memoryUsage: (typeof performance !== 'undefined' && performance.memory) ? {
        usedJSHeapSize: (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB',
        totalJSHeapSize: (performance.memory.totalJSHeapSize / 1048576).toFixed(2) + ' MB',
        jsHeapSizeLimit: (performance.memory.jsHeapSizeLimit / 1048576).toFixed(2) + ' MB'
      } : null
    };
  }

  // Clean up all resources
  cleanup() {
    console.log('🧵 Thread Manager: Cleaning up all resources...');

    // Cancel all running operations
    for (const [id, operation] of this.operations) {
      if (operation.status === 'running' && operation.cancelFn) {
        try {
          operation.cancelFn();
        } catch (error) {
          console.error('Failed to cancel operation:', error);
        }
      }
      clearTimeout(operation.timeoutId);
      if (operation.warningId) clearTimeout(operation.warningId);
    }

    // Terminate all workers
    for (const [id, workerInfo] of this.workers) {
      try {
        workerInfo.worker.terminate();
      } catch (error) {
        console.error('Failed to terminate worker:', error);
      }
    }

    // Clear all timers and intervals
    for (const [id, timer] of this.timers) {
      clearTimeout(timer.timerId);
    }
    for (const [id, interval] of this.intervals) {
      clearInterval(interval.timerId);
    }

    // Clear all collections
    this.operations.clear();
    this.workers.clear();
    this.timers.clear();
    this.intervals.clear();
  }
}

// Export singleton instance
export const threadManager = new ThreadManager();

// Helper function to track async operations
export function trackAsync(name, asyncFn, options = {}) {
  const operation = threadManager.registerOperation(name, options);
  
  return asyncFn()
    .then(result => {
      operation.complete(result);
      return result;
    })
    .catch(error => {
      operation.fail(error);
      throw error;
    });
}

// Helper function to create tracked timers
export function trackedTimeout(fn, delay, name = 'timeout') {
  const timerId = setTimeout(() => {
    threadManager.unregisterTimer(id);
    fn();
  }, delay);
  
  const id = threadManager.registerTimer(name, timerId, 'timeout', delay);
  return { timerId, trackingId: id };
}

// Helper function to create tracked intervals
export function trackedInterval(fn, delay, name = 'interval') {
  const intervalId = setInterval(fn, delay);
  const id = threadManager.registerTimer(name, intervalId, 'interval', delay);
  return { intervalId, trackingId: id };
}