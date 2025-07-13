import axios from 'axios'
import { useUserStore } from '@/stores/userStore'

let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  
  failedQueue = []
}

// Request interceptor to add auth token
axios.interceptors.request.use(
  (config) => {
    // Skip auth header for non-authenticated endpoints
    const publicEndpoints = [
      '/api/health',
      '/api/auth/google/login',
      '/api/auth/google/callback',
      '/api/auth/refresh'
    ]
    
    const isPublicEndpoint = publicEndpoints.some(endpoint => 
      config.url.includes(endpoint)
    )
    
    if (!isPublicEndpoint) {
      const userStore = useUserStore()
      if (userStore.accessToken) {
        config.headers.Authorization = `Bearer ${userStore.accessToken}`
      }
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle 401s
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const userStore = useUserStore()
    
    // If error is 401 and we have a refresh token
    if (error.response?.status === 401 && !originalRequest._retry && userStore.refreshToken) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return axios(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }
      
      originalRequest._retry = true
      isRefreshing = true
      
      try {
        await userStore.refreshAccessToken()
        const newToken = userStore.accessToken
        processQueue(null, newToken)
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return axios(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        userStore.clearAuth()
        // Don't log 401 errors to console
        if (error.response?.status !== 401) {
          return Promise.reject(error)
        }
        // Return a handled 401 error without logging
        const silentError = new Error('Authentication required')
        silentError.response = error.response
        silentError.handled = true
        return Promise.reject(silentError)
      } finally {
        isRefreshing = false
      }
    }
    
    // For auth endpoints, don't log 401 errors
    const authEndpoints = ['/api/auth/', '/api/user/', '/api/admin/']
    const isAuthEndpoint = authEndpoints.some(endpoint => error.config?.url?.includes(endpoint))
    
    if (error.response?.status === 401 && isAuthEndpoint) {
      // Return a handled error that won't be logged
      const silentError = new Error('Authentication required')
      silentError.response = error.response
      silentError.handled = true
      return Promise.reject(silentError)
    }
    
    return Promise.reject(error)
  }
)

export default axios