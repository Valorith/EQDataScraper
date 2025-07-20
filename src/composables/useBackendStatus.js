/**
 * Composable for monitoring backend connection status
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getApiBaseUrl } from '../config/api'
import { discoverBackendUrl, getCurrentBackendUrl, clearDiscoveryCache } from '../utils/backendDiscovery'

export function useBackendStatus() {
  const backendUrl = ref(getApiBaseUrl())
  const isConnected = ref(false)
  const isChecking = ref(false)
  const lastCheckTime = ref(null)
  const errorCount = ref(0)
  
  let checkInterval = null
  let retryTimeout = null
  
  // Computed properties
  const statusMessage = computed(() => {
    if (isChecking.value) return 'Checking connection...'
    if (isConnected.value) return `Connected to ${backendUrl.value}`
    if (errorCount.value > 3) return 'Backend unavailable - retrying periodically'
    return 'Connecting to backend...'
  })
  
  const statusClass = computed(() => {
    if (isConnected.value) return 'success'
    if (errorCount.value > 3) return 'error'
    return 'warning'
  })
  
  // Check backend health
  async function checkBackendHealth() {
    if (isChecking.value) return
    
    isChecking.value = true
    
    try {
      // Always get fresh backend URL
      const currentUrl = getCurrentBackendUrl() || backendUrl.value
      
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)
      
      const response = await fetch(`${currentUrl}/api/health`, {
        signal: controller.signal,
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        },
        cache: 'no-cache'
      })
      
      clearTimeout(timeoutId)
      
      if (response.ok) {
        const data = await response.json()
        if (data.status === 'healthy') {
          const wasDisconnected = !isConnected.value
          isConnected.value = true
          errorCount.value = 0
          lastCheckTime.value = new Date()
          backendUrl.value = currentUrl
          
          if (wasDisconnected) {
            console.log('✅ Backend connection restored')
            // Update check interval for connected state
            resetCheckInterval()
          }
        } else {
          throw new Error('Backend unhealthy')
        }
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      const wasConnected = isConnected.value
      isConnected.value = false
      errorCount.value++
      
      // Only log first few errors to avoid spam
      if (errorCount.value <= 3) {
        console.debug(`Backend health check failed (attempt ${errorCount.value}):`, error.message)
      }
      
      // Trigger rediscovery after multiple failures
      if (errorCount.value === 3 || (wasConnected && errorCount.value === 1)) {
        console.log('Backend connection lost, attempting rediscovery...')
        await discoverBackend()
      }
      
      if (wasConnected) {
        // Update check interval for disconnected state
        resetCheckInterval()
      }
    } finally {
      isChecking.value = false
    }
  }
  
  // Discover backend
  async function discoverBackend() {
    try {
      // Force clear cache for fresh discovery
      clearDiscoveryCache()
      
      const newUrl = await discoverBackendUrl()
      if (newUrl !== backendUrl.value) {
        console.log('Backend URL updated:', newUrl)
        backendUrl.value = newUrl
        errorCount.value = 0 // Reset error count on URL change
        // Immediately check health with new URL
        await checkBackendHealth()
      } else if (!isConnected.value) {
        // Even if URL is same, try checking health again
        await checkBackendHealth()
      }
    } catch (error) {
      console.error('Backend discovery failed:', error)
      // Schedule retry
      if (!retryTimeout) {
        retryTimeout = setTimeout(() => {
          retryTimeout = null
          if (!isConnected.value) {
            discoverBackend()
          }
        }, 5000) // Retry after 5 seconds
      }
    }
  }
  
  // Reset check interval based on connection status
  function resetCheckInterval() {
    if (checkInterval) {
      clearInterval(checkInterval)
    }
    
    const interval = isConnected.value ? 30000 : 10000 // 30s when connected, 10s when not
    checkInterval = setInterval(() => {
      checkBackendHealth()
    }, interval)
  }
  
  // Start monitoring
  function startMonitoring() {
    // Initial check
    checkBackendHealth()
    
    // Set up regular health checks
    resetCheckInterval()
  }
  
  // Stop monitoring
  function stopMonitoring() {
    if (checkInterval) {
      clearInterval(checkInterval)
      checkInterval = null
    }
    if (retryTimeout) {
      clearTimeout(retryTimeout)
      retryTimeout = null
    }
  }
  
  // Manual refresh
  async function refresh() {
    errorCount.value = 0
    await discoverBackend()
    await checkBackendHealth()
  }
  
  // Lifecycle
  onMounted(() => {
    startMonitoring()
  })
  
  onUnmounted(() => {
    stopMonitoring()
  })
  
  return {
    backendUrl,
    isConnected,
    isChecking,
    lastCheckTime,
    errorCount,
    statusMessage,
    statusClass,
    refresh,
    checkBackendHealth
  }
}