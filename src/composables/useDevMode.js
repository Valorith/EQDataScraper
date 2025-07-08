import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '../config/api'

// Shared state for dev mode across the app
// Use a global state object to survive hot reloads
if (!window._devModeState) {
  // Initialize from sessionStorage if available (to persist across hot reloads)
  const storedDevAuth = sessionStorage.getItem('dev_auth_enabled')
  const storedCheckComplete = sessionStorage.getItem('dev_auth_check_complete')
  const storedLastCheck = sessionStorage.getItem('dev_auth_last_check')
  
  window._devModeState = {
    isDevAuthEnabled: ref(storedDevAuth === 'true'),
    devAuthCheckComplete: ref(storedCheckComplete === 'true'),
    isChecking: ref(false),
    lastCheckTime: storedLastCheck ? parseInt(storedLastCheck) : 0
  }
  
  // Log restoration status (dev mode only)
  if (import.meta.env.MODE === 'development' && storedDevAuth) {
    console.log(`🔧 Restored dev auth state from sessionStorage: ${storedDevAuth}`)
  }
} else {
  // Hot reload detected - preserve existing state
  if (import.meta.hot) {
    const storedDevAuth = sessionStorage.getItem('dev_auth_enabled')
    
    // If sessionStorage has newer data, update the global state
    if (storedDevAuth && window._devModeState.isDevAuthEnabled.value !== (storedDevAuth === 'true')) {
      window._devModeState.isDevAuthEnabled.value = storedDevAuth === 'true'
    }
  }
}

// Extract refs from global state
const { isDevAuthEnabled, devAuthCheckComplete, isChecking } = window._devModeState

// Watch for changes and persist to sessionStorage (only set up once)
if (!window._devModeWatchersSetup) {
  watch(isDevAuthEnabled, (newValue) => {
    sessionStorage.setItem('dev_auth_enabled', String(newValue))
  }, { immediate: false })

  watch(devAuthCheckComplete, (newValue) => {
    sessionStorage.setItem('dev_auth_check_complete', String(newValue))
  }, { immediate: false })
  
  window._devModeWatchersSetup = true
}

export function useDevMode() {
  const isProduction = computed(() => import.meta.env.PROD)
  
  const checkDevAuthStatus = async (forceCheck = false) => {
    const appMode = import.meta.env.VITE_APP_MODE || 'undefined'
    const now = Date.now()
    const timeSinceLastCheck = now - window._devModeState.lastCheckTime
    
    if (import.meta.env.MODE === 'development') {
      console.log(`🔧 Dev Auth Check: Starting (App Mode: ${appMode}, Force: ${forceCheck})`)
    }
    
    // If we're not in custom dev mode but auth is enabled, clear it immediately
    if (appMode !== 'development' && isDevAuthEnabled.value) {
      isDevAuthEnabled.value = false
      devAuthCheckComplete.value = true
      sessionStorage.removeItem('dev_auth_enabled')
      sessionStorage.setItem('dev_auth_last_check', String(now))
      window._devModeState.lastCheckTime = now
      return
    }
    
    // CRITICAL: Never enable dev auth in production builds
    if (isProduction.value) {
      isDevAuthEnabled.value = false
      devAuthCheckComplete.value = true
      return
    }
    
    // Only enable dev auth if explicitly in custom development mode
    if (appMode === 'development') {
      isDevAuthEnabled.value = true
      devAuthCheckComplete.value = true
      sessionStorage.setItem('dev_auth_enabled', 'true')
      sessionStorage.setItem('dev_auth_last_check', String(now))
      window._devModeState.lastCheckTime = now
      return
    }
    
    // Skip if already checking
    if (isChecking.value && !forceCheck) {
      return
    }
    
    // Skip if recently checked (unless forced) - prevent excessive API calls
    // For hot reloads, reduce the check interval to 5 seconds instead of 10
    const minCheckInterval = import.meta.hot ? 5000 : 10000
    if (devAuthCheckComplete.value && !forceCheck && timeSinceLastCheck < minCheckInterval) {
      return
    }
    
    // Special handling for hot reload: if we have a cached value and it's recent, use it
    if (import.meta.hot && timeSinceLastCheck < 30000) { // 30 seconds
      const cachedValue = sessionStorage.getItem('dev_auth_enabled')
      if (cachedValue !== null) {
        isDevAuthEnabled.value = cachedValue === 'true'
        devAuthCheckComplete.value = true
        return
      }
    }
    
    isChecking.value = true
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/auth/dev-status`, {
        timeout: 5000 // Reduced timeout since we have fallback logic
      })
      
      // Double-check that we're not in production
      if (isProduction.value) {
        isDevAuthEnabled.value = false
      } else {
        isDevAuthEnabled.value = response.data.dev_auth_enabled || false
        if (import.meta.env.MODE === 'development') {
          console.log(`✅ Dev auth status: ${isDevAuthEnabled.value ? 'ENABLED' : 'DISABLED'}`)
        }
      }
      
      devAuthCheckComplete.value = true
      window._devModeState.lastCheckTime = now
      sessionStorage.setItem('dev_auth_last_check', String(now))
    } catch (err) {
      // In our custom development mode, fallback to enabled if backend is unavailable
      if (import.meta.env.VITE_APP_MODE === 'development') {
        isDevAuthEnabled.value = true
        sessionStorage.setItem('dev_auth_enabled', 'true')
      } else {
        isDevAuthEnabled.value = false
        sessionStorage.removeItem('dev_auth_enabled')
      }
      
      devAuthCheckComplete.value = true
      window._devModeState.lastCheckTime = now
      sessionStorage.setItem('dev_auth_last_check', String(now))
    } finally {
      isChecking.value = false
    }
  }
  
  // Helper function to reset dev mode state (useful for debugging)
  const resetDevModeState = () => {
    if (import.meta.env.MODE === 'development') {
      console.log('🔄 Resetting dev mode state')
    }
    isDevAuthEnabled.value = false
    devAuthCheckComplete.value = false
    isChecking.value = false
    window._devModeState.lastCheckTime = 0
    sessionStorage.removeItem('dev_auth_enabled')
    sessionStorage.removeItem('dev_auth_check_complete')
    sessionStorage.removeItem('dev_auth_last_check')
  }
  
  // Helper function to force refresh dev mode status
  const refreshDevModeStatus = async () => {
    if (import.meta.env.MODE === 'development') {
      console.log('🔄 Force refreshing dev mode status')
    }
    devAuthCheckComplete.value = false
    window._devModeState.lastCheckTime = 0
    await checkDevAuthStatus(true)
  }
  
  return {
    isDevAuthEnabled,  // Return the ref directly, not wrapped in computed
    devAuthCheckComplete,
    isChecking,
    checkDevAuthStatus,
    resetDevModeState,
    refreshDevModeStatus
  }
}