// Worker Manager for handling Web Worker communications
import { API_BASE_URL } from '@/config/api';

class WorkerManager {
  constructor() {
    this.worker = null;
    this.pendingRequests = new Map();
    this.requestId = 0;
  }

  // Initialize the worker (lazy loading)
  initWorker() {
    if (!this.worker && typeof Worker !== 'undefined') {
      try {
        this.worker = new Worker(
          new URL('../workers/authWorker.js', import.meta.url),
          { type: 'module' }
        );
        
        this.worker.addEventListener('message', (event) => {
          this.handleWorkerMessage(event.data);
        });
        
        this.worker.addEventListener('error', (error) => {
          console.error('Worker error:', error);
          this.cleanup();
        });
      } catch (error) {
        console.error('Failed to initialize worker:', error);
      }
    }
  }

  // Handle messages from worker
  handleWorkerMessage(data) {
    const { type, payload, requestId } = data;
    
    if (requestId && this.pendingRequests.has(requestId)) {
      const { resolve, reject } = this.pendingRequests.get(requestId);
      this.pendingRequests.delete(requestId);
      
      if (type === 'ERROR') {
        reject(new Error(payload.message || 'Worker operation failed'));
      } else {
        resolve(payload);
      }
    }
  }

  // Send message to worker and return promise
  sendMessage(type, payload) {
    return new Promise((resolve, reject) => {
      if (!this.worker) {
        this.initWorker();
      }
      
      if (!this.worker) {
        // Fallback if worker initialization failed
        reject(new Error('Worker not available'));
        return;
      }
      
      const requestId = ++this.requestId;
      this.pendingRequests.set(requestId, { resolve, reject });
      
      // Set timeout for worker operations
      const timeout = setTimeout(() => {
        if (this.pendingRequests.has(requestId)) {
          this.pendingRequests.delete(requestId);
          reject(new Error('Worker operation timeout'));
        }
      }, 5000); // 5 second timeout
      
      // Clear timeout on completion
      const originalResolve = resolve;
      const originalReject = reject;
      
      this.pendingRequests.set(requestId, {
        resolve: (result) => {
          clearTimeout(timeout);
          originalResolve(result);
        },
        reject: (error) => {
          clearTimeout(timeout);
          originalReject(error);
        }
      });
      
      this.worker.postMessage({ type, payload, requestId });
    });
  }

  // Verify token using worker
  async verifyToken(token) {
    try {
      const result = await this.sendMessage('VERIFY_TOKEN', {
        token,
        apiBaseUrl: API_BASE_URL
      });
      return result;
    } catch (error) {
      console.error('Worker verify token failed:', error);
      throw error;
    }
  }

  // Refresh token using worker
  async refreshToken(refreshToken) {
    try {
      const result = await this.sendMessage('REFRESH_TOKEN', {
        refreshToken,
        apiBaseUrl: API_BASE_URL
      });
      return result;
    } catch (error) {
      console.error('Worker refresh token failed:', error);
      throw error;
    }
  }

  // Parse JWT using worker
  async parseJWT(token) {
    try {
      const result = await this.sendMessage('PARSE_JWT', { token });
      return result;
    } catch (error) {
      console.error('Worker parse JWT failed:', error);
      throw error;
    }
  }

  // Cleanup worker
  cleanup() {
    if (this.worker) {
      this.worker.terminate();
      this.worker = null;
    }
    this.pendingRequests.clear();
  }
}

// Export singleton instance
export const workerManager = new WorkerManager();