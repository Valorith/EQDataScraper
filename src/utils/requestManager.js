// Request Manager for handling cancellable requests and preventing request pile-up
import axios from 'axios';

class RequestManager {
  constructor() {
    this.pendingRequests = new Map();
  }

  // Create a cancellable request
  createCancellableRequest(key) {
    // Cancel any existing request with the same key
    this.cancelRequest(key);
    
    // Create new abort controller
    const controller = new AbortController();
    this.pendingRequests.set(key, controller);
    
    return {
      signal: controller.signal,
      cancel: () => this.cancelRequest(key)
    };
  }

  // Cancel a specific request
  cancelRequest(key) {
    const controller = this.pendingRequests.get(key);
    if (controller) {
      controller.abort();
      this.pendingRequests.delete(key);
    }
  }

  // Cancel all pending requests
  cancelAllRequests() {
    this.pendingRequests.forEach((controller) => {
      controller.abort();
    });
    this.pendingRequests.clear();
  }

  // Get cancel token for axios (compatibility layer)
  getCancelToken(key) {
    // Cancel any existing request with the same key
    this.cancelRequest(key);
    
    // Create new cancel token source
    const source = axios.CancelToken.source();
    
    // Store controller-like object for compatibility
    const controller = {
      abort: () => source.cancel('Request cancelled'),
      signal: source.token
    };
    this.pendingRequests.set(key, controller);
    
    return source.token;
  }

  // Make a cancellable axios request
  async request(config, key = null) {
    if (key) {
      const { signal } = this.createCancellableRequest(key);
      config.signal = signal;
    }

    try {
      const response = await axios(config);
      if (key) {
        this.pendingRequests.delete(key);
      }
      return response;
    } catch (error) {
      if (key) {
        this.pendingRequests.delete(key);
      }
      
      // Check if request was cancelled
      if (error.name === 'CanceledError' || error.code === 'ERR_CANCELED') {
        console.log(`Request cancelled: ${key || 'unknown'}`);
        return null;
      }
      
      throw error;
    }
  }

  // Convenience methods
  async get(url, config = {}, key = null) {
    return this.request({ ...config, method: 'GET', url }, key);
  }

  async post(url, data, config = {}, key = null) {
    return this.request({ ...config, method: 'POST', url, data }, key);
  }

  // Clean up on page unload
  cleanup() {
    this.cancelAllRequests();
  }
}

// Export singleton instance
export const requestManager = new RequestManager();

// Add cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    requestManager.cleanup();
  });
}