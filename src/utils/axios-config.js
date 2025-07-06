import axios from 'axios'

// Track rate limit warnings to avoid console spam
let rateLimitWarningShown = false
let lastRateLimitWarning = 0

// Configure axios defaults
export function configureAxios() {
  // Add response interceptor to handle common errors
  axios.interceptors.response.use(
    response => response,
    error => {
      // Handle rate limiting silently for certain endpoints
      if (error.response?.status === 429) {
        const url = error.config?.url || ''
        const now = Date.now()
        
        // Only show rate limit warning once every 30 seconds
        if (!rateLimitWarningShown || now - lastRateLimitWarning > 30000) {
          console.warn(`Rate limit reached for ${url}. Retrying later...`)
          rateLimitWarningShown = true
          lastRateLimitWarning = now
        }
        
        // Don't log error for health checks and cache status
        if (url.includes('/api/health') || url.includes('/api/cache')) {
          return Promise.reject(error)
        }
      }
      
      // Handle auth errors silently for admin endpoints
      if (error.response?.status === 401 && error.config?.url?.includes('/api/admin')) {
        // Admin endpoints require auth, this is expected in dev mode
        return Promise.reject(error)
      }
      
      return Promise.reject(error)
    }
  )
}

export default axios