// Tracked Axios - Wrapper around axios that automatically tracks all HTTP requests
import axios from 'axios'
import { threadManager } from './threadManager'

// Create a tracked axios instance
const trackedAxios = axios.create()

// Request interceptor to track operations
trackedAxios.interceptors.request.use(
  (config) => {
    // Generate operation name
    const method = config.method?.toUpperCase() || 'GET'
    const url = config.url || 'unknown'
    const operationName = `${method} ${url}`
    
    // Track the operation
    const operation = threadManager.registerOperation(operationName, {
      type: 'http',
      timeout: config.timeout || 30000,
      metadata: {
        method,
        url,
        params: config.params,
        data: config.data ? '[data]' : undefined
      },
      cancelFn: () => {
        if (config.cancelToken) {
          config.cancelToken.cancel('Operation cancelled by thread manager')
        }
      }
    })
    
    // Attach operation ID to config for response tracking
    config._operationId = operation.id
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to complete operations
trackedAxios.interceptors.response.use(
  (response) => {
    // Complete the operation
    if (response.config._operationId) {
      threadManager.completeOperation(response.config._operationId, {
        status: response.status,
        statusText: response.statusText
      })
    }
    return response
  },
  (error) => {
    // Fail the operation
    if (error.config?._operationId) {
      threadManager.failOperation(error.config._operationId, error)
    }
    return Promise.reject(error)
  }
)

// Export both the tracked instance and helper methods
export default trackedAxios

// Helper to create a tracked request with custom operation name
export function trackedRequest(operationName, requestFn, options = {}) {
  const operation = threadManager.registerOperation(operationName, {
    type: 'custom',
    ...options
  })
  
  return requestFn()
    .then(result => {
      operation.complete(result)
      return result
    })
    .catch(error => {
      operation.fail(error)
      throw error
    })
}

// Helper to track Vue component lifecycle operations
export function trackLifecycle(componentName, lifecycleName, fn) {
  return trackedRequest(
    `${componentName}.${lifecycleName}`,
    fn,
    {
      type: 'lifecycle',
      warningThreshold: 2000,
      timeout: 10000
    }
  )
}

// Helper to track Vuex/Pinia actions
export function trackAction(storeName, actionName, fn) {
  return trackedRequest(
    `${storeName}.${actionName}`,
    fn,
    {
      type: 'store-action',
      warningThreshold: 3000,
      timeout: 15000
    }
  )
}