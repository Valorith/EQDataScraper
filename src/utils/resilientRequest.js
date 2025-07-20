/**
 * Resilient Request Utility
 * Provides automatic backend discovery and retry logic for API requests
 */

import { getApiBaseUrl } from '../config/api'
import { discoverBackendUrl, clearDiscoveryCache } from './backendDiscovery'
import { requestManager } from './requestManager'

/**
 * Make a resilient request that can handle backend URL changes
 * @param {string} endpoint - The API endpoint (e.g., '/api/health')
 * @param {object} config - Request configuration (method, headers, body, etc.)
 * @param {string} key - Optional request key for cancellation
 * @returns {Promise} The response from the API
 */
export async function resilientRequest(endpoint, config = {}, key = null) {
  // Ensure endpoint starts with /
  if (!endpoint.startsWith('/')) {
    endpoint = '/' + endpoint
  }
  
  // First attempt with current URL
  const currentUrl = getApiBaseUrl()
  try {
    const url = `${currentUrl}${endpoint}`
    const response = await requestManager.request({
      ...config,
      url,
      timeout: config.timeout || 5000
    }, key)
    
    return response
  } catch (error) {
    // If it's a network error (not 4xx or 5xx), try to rediscover the backend
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED' || 
        error.message?.includes('timeout') || !error.response) {
      console.warn('Backend request failed, attempting to rediscover...')
      
      // Clear the cache to force rediscovery
      clearDiscoveryCache()
      
      try {
        // Rediscover the backend
        const newUrl = await discoverBackendUrl()
        
        // If we found a different URL, try again
        if (newUrl !== currentUrl) {
          console.log(`Retrying with discovered URL: ${newUrl}`)
          const url = `${newUrl}${endpoint}`
          const response = await requestManager.request({
            ...config,
            url,
            timeout: config.timeout || 5000
          }, key)
          
          return response
        }
      } catch (discoveryError) {
        console.error('Backend rediscovery failed:', discoveryError)
      }
    }
    
    // Re-throw the original error
    throw error
  }
}

/**
 * Convenience methods for common HTTP verbs
 */
export const resilientApi = {
  async get(endpoint, config = {}, key = null) {
    return resilientRequest(endpoint, { ...config, method: 'GET' }, key)
  },
  
  async post(endpoint, data, config = {}, key = null) {
    return resilientRequest(endpoint, { 
      ...config, 
      method: 'POST', 
      data,
      headers: {
        'Content-Type': 'application/json',
        ...config.headers
      }
    }, key)
  },
  
  async put(endpoint, data, config = {}, key = null) {
    return resilientRequest(endpoint, { 
      ...config, 
      method: 'PUT', 
      data,
      headers: {
        'Content-Type': 'application/json',
        ...config.headers
      }
    }, key)
  },
  
  async delete(endpoint, config = {}, key = null) {
    return resilientRequest(endpoint, { ...config, method: 'DELETE' }, key)
  }
}

export default resilientApi