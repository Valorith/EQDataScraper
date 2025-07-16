// Performance utilities for preventing UI blocking

/**
 * Debounce function - delays execution until after wait milliseconds have elapsed
 * since the last time the debounced function was invoked
 */
export function debounce(func, wait = 300) {
  let timeout;
  let lastArgs;
  
  const debounced = function(...args) {
    lastArgs = args;
    clearTimeout(timeout);
    
    timeout = setTimeout(() => {
      func.apply(this, lastArgs);
    }, wait);
  };
  
  debounced.cancel = function() {
    clearTimeout(timeout);
    timeout = null;
  };
  
  debounced.flush = function() {
    if (timeout) {
      clearTimeout(timeout);
      func.apply(this, lastArgs);
    }
  };
  
  return debounced;
}

/**
 * Throttle function - ensures function is called at most once per specified time period
 */
export function throttle(func, limit = 300) {
  let inThrottle;
  let lastFunc;
  let lastRan;
  
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      lastRan = Date.now();
      inThrottle = true;
    } else {
      clearTimeout(lastFunc);
      lastFunc = setTimeout(() => {
        if ((Date.now() - lastRan) >= limit) {
          func.apply(this, args);
          lastRan = Date.now();
        }
      }, Math.max(limit - (Date.now() - lastRan), 0));
    }
  };
}

/**
 * Defer heavy operations to idle time
 */
export function deferToIdle(func, timeout = 2000) {
  if ('requestIdleCallback' in window) {
    return window.requestIdleCallback(func, { timeout });
  }
  // Fallback for browsers that don't support requestIdleCallback
  return setTimeout(func, 100);
}

/**
 * Cancel idle callback
 */
export function cancelIdleCallback(id) {
  if ('cancelIdleCallback' in window) {
    window.cancelIdleCallback(id);
  } else {
    clearTimeout(id);
  }
}

/**
 * Run function on next animation frame
 */
export function nextFrame(func) {
  return requestAnimationFrame(func);
}

/**
 * Batch DOM updates using requestAnimationFrame
 */
export function batchUpdate(updates) {
  requestAnimationFrame(() => {
    updates.forEach(update => update());
  });
}

/**
 * Create a promise that resolves after a specified delay
 */
export function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Check if the main thread is idle
 */
export function isMainThreadIdle() {
  return new Promise(resolve => {
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => resolve(true), { timeout: 100 });
    } else {
      setTimeout(() => resolve(true), 100);
    }
  });
}

/**
 * Chunk array processing to avoid blocking the UI
 */
export async function* chunkProcess(array, chunkSize = 100) {
  for (let i = 0; i < array.length; i += chunkSize) {
    yield array.slice(i, i + chunkSize);
    // Allow UI to update between chunks
    await isMainThreadIdle();
  }
}

/**
 * Process large array without blocking UI
 */
export async function processArrayAsync(array, processor, chunkSize = 100) {
  const results = [];
  
  for await (const chunk of chunkProcess(array, chunkSize)) {
    const chunkResults = chunk.map(processor);
    results.push(...chunkResults);
  }
  
  return results;
}