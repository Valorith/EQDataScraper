/**
 * Axios configuration and interceptors
 */

import axios from 'axios'

// Set a reasonable default timeout for all requests
axios.defaults.timeout = 10000 // 10 seconds

// Track rate limit warnings to avoid console spam
let rateLimitWarningShown = false
let lastRateLimitWarning = 0

// Add response interceptor to handle common errors
axios.interceptors.response.use(
  response => response,
  error => {
    // Check if error was already handled by auth interceptor
    if (error.handled) {
      return Promise.reject(error)
    }
    
    // Suppress console errors for expected cases
    if (error.config?.suppressErrors) {
      return Promise.reject(error)
    }

    // Handle timeout errors specially
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      const url = error.config?.url || ''
      // Only log timeouts for non-auth endpoints
      if (!url.includes('/api/auth/') && !url.includes('/api/user/')) {
        console.warn(`Request timeout: ${url}`)
      }
      return Promise.reject(error)
    }
    
    // Handle specific error cases silently
    if (error.response) {
      const status = error.response.status
      const url = error.config?.url || ''
      
      // Silent handling for 404s on admin endpoints
      if (status === 404 && url.includes('/api/admin/')) {
        // Admin endpoints may not exist if OAuth is disabled
        return Promise.reject(error)
      }
      
      // Silent handling for 401s on auth/admin endpoints
      if (status === 401) {
        const authEndpoints = ['/api/auth/', '/api/user/', '/api/admin/']
        if (authEndpoints.some(endpoint => url.includes(endpoint))) {
          // Expected when not authenticated
          return Promise.reject(error)
        }
      }
      
      // Handle rate limiting with smart warning
      if (status === 429) {
        const now = Date.now()
        // Only show rate limit warning once every 30 seconds
        if (!rateLimitWarningShown || now - lastRateLimitWarning > 30000) {
          console.warn(`Rate limit reached. Retrying later...`)
          rateLimitWarningShown = true
          lastRateLimitWarning = now
        }
        return Promise.reject(error)
      }
    }
    
    // Let other errors bubble up with logging
    console.error('API Error:', error.message)
    return Promise.reject(error)
  }
)

// Helper to make requests with error suppression
export const silentRequest = (config) => {
  return axios({
    ...config,
    suppressErrors: true
  })
}

export default axios