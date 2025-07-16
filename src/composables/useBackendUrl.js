/**
 * Vue Composable for Backend URL Management
 * Provides reactive backend URL and discovery status
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getApiBaseUrl } from '../config/api'
import { discoverBackendUrl, getCurrentBackendUrl } from '../utils/backendDiscovery'

export function useBackendUrl() {
  const backendUrl = ref(getApiBaseUrl())
  const isDiscovering = ref(false)
  const discoveryError = ref(null)
  
  // Update interval to check for URL changes
  let updateInterval = null
  
  const updateUrl = () => {
    const currentUrl = getCurrentBackendUrl() || getApiBaseUrl()
    if (currentUrl !== backendUrl.value) {
      backendUrl.value = currentUrl
      console.log('Backend URL updated to:', currentUrl)
    }
  }
  
  const rediscoverBackend = async () => {
    isDiscovering.value = true
    discoveryError.value = null
    
    try {
      const url = await discoverBackendUrl()
      backendUrl.value = url
      return url
    } catch (error) {
      discoveryError.value = error
      console.error('Backend discovery failed:', error)
      throw error
    } finally {
      isDiscovering.value = false
    }
  }
  
  onMounted(() => {
    // Initial update
    updateUrl()
    
    // Check for URL changes periodically
    updateInterval = setInterval(updateUrl, 5000)
    
    // Trigger discovery if in development and no discovered URL yet
    if (!import.meta.env.PROD && !getCurrentBackendUrl()) {
      rediscoverBackend().catch(() => {
        // Silently handle discovery failure on mount
      })
    }
  })
  
  onUnmounted(() => {
    if (updateInterval) {
      clearInterval(updateInterval)
    }
  })
  
  return {
    backendUrl: computed(() => backendUrl.value),
    isDiscovering: computed(() => isDiscovering.value),
    discoveryError: computed(() => discoveryError.value),
    rediscoverBackend
  }
}