/**
 * Enhanced API Client with automatic retry and backend discovery
 */

import axios from 'axios'
import { getApiBaseUrl } from '../config/api'
import { discoverBackendUrl, clearDiscoveryCache } from './backendDiscovery'

// Create axios instance with default config
const apiClient = axios.create({
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// Track failed attempts to prevent spam
let consecutiveFailures = 0
let lastFailureTime = 0
const FAILURE_BACKOFF_TIME = 30000 // 30 seconds

// Request interceptor to add base URL dynamically
apiClient.interceptors.request.use(
  async (config) => {
    // Get current backend URL
    const baseURL = getApiBaseUrl()
    config.baseURL = baseURL
    
    // Add timestamp to prevent caching issues
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now()
      }
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling and retry
apiClient.interceptors.response.use(
  (response) => {
    // Reset failure counter on success
    consecutiveFailures = 0
    return response
  },
  async (error) => {
    const originalRequest = error.config
    
    // Don't retry if it's not a network error
    if (error.response && error.response.status < 500) {
      return Promise.reject(error)
    }
    
    // Check if we're in backoff period
    if (consecutiveFailures > 3 && (Date.now() - lastFailureTime) < FAILURE_BACKOFF_TIME) {
      console.debug('API client in backoff period, not retrying')
      return Promise.reject(error)
    }
    
    // If network error and not already retried
    const isNetworkError = error.code === 'ECONNABORTED' || 
                          error.code === 'ERR_NETWORK' || 
                          error.code === 'ECONNREFUSED' ||
                          error.message?.includes('Network Error') ||
                          error.message?.includes('fetch failed') ||
                          (!error.response && error.request)
    
    if (!originalRequest._retry && isNetworkError) {
      originalRequest._retry = true
      consecutiveFailures++
      lastFailureTime = Date.now()
      
      if (consecutiveFailures <= 1) {
        console.log('Network error detected, attempting backend rediscovery...')
      }
      
      try {
        // Clear cache and rediscover
        clearDiscoveryCache()
        const newUrl = await discoverBackendUrl()
        
        // Update the request with new URL
        originalRequest.baseURL = newUrl
        
        // Retry the request
        return apiClient(originalRequest)
      } catch (retryError) {
        // Only log on first few failures to reduce console spam
        if (consecutiveFailures <= 2) {
          console.debug('Backend discovery retry failed')
        }
        return Promise.reject(retryError)
      }
    }
    
    return Promise.reject(error)
  }
)

// Helper functions for common HTTP methods
export const api = {
  get: (url, config) => apiClient.get(url, config),
  post: (url, data, config) => apiClient.post(url, data, config),
  put: (url, data, config) => apiClient.put(url, data, config),
  delete: (url, config) => apiClient.delete(url, config),
  patch: (url, data, config) => apiClient.patch(url, data, config)
}

// Export the raw client for advanced usage
export default apiClient