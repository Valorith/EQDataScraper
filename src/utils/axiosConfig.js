/**
 * Axios configuration and interceptors
 */

import axios from 'axios'

// Add response interceptor to handle common errors
axios.interceptors.response.use(
  response => response,
  error => {
    // Suppress console errors for expected cases
    if (error.config?.suppressErrors) {
      return Promise.reject(error)
    }

    // Handle specific error cases silently
    if (error.response) {
      const status = error.response.status
      const url = error.config?.url || ''
      
      // Silent handling for common cases
      if (status === 404 && url.includes('/api/admin/')) {
        // Admin endpoints may not exist if OAuth is disabled
        return Promise.reject(error)
      }
      
      if (status === 401 && url.includes('/api/admin/')) {
        // Authentication required for admin endpoints
        return Promise.reject(error)
      }
      
      if (status === 429) {
        // Rate limiting - expected behavior
        return Promise.reject(error)
      }
    }
    
    // Let other errors bubble up
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