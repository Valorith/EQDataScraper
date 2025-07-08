import { ref, computed } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '../config/api'

// Shared state for dev mode across the app
// Initialize from sessionStorage if available (to persist across hot reloads)
const storedDevAuth = sessionStorage.getItem('dev_auth_enabled')
// Only enable dev auth when explicitly set - do not auto-enable based on Vite mode
// Clear stale sessionStorage and start fresh each time
sessionStorage.removeItem('dev_auth_enabled')
const isDevAuthEnabled = ref(false)  // Start disabled, let backend check determine state
const devAuthCheckComplete = ref(false)  // Always check backend on startup
const isChecking = ref(false)

// Watch for changes and persist to sessionStorage
import { watch } from 'vue'
watch(isDevAuthEnabled, (newValue) => {
  console.log('🔧 Persisting dev auth state to sessionStorage:', newValue)
  sessionStorage.setItem('dev_auth_enabled', String(newValue))
})

export function useDevMode() {
  const isProduction = computed(() => import.meta.env.PROD)
  
  const checkDevAuthStatus = async (forceCheck = false) => {
    const appMode = import.meta.env.VITE_APP_MODE || 'undefined'
    console.log(`🔧 Dev Auth Check: Starting (App Mode: ${appMode}, Force: ${forceCheck})`)
    console.log(`   Current state: Checking=${isChecking.value}, Complete=${devAuthCheckComplete.value}, Enabled=${isDevAuthEnabled.value}`)
    
    // Skip if already checking
    if (isChecking.value && !forceCheck) {
      console.log('⏭️  Skipping: Dev auth check already in progress')
      return
    }
    
    // Skip if already checked (unless forced)
    if (devAuthCheckComplete.value && !forceCheck) {
      console.log(`✅ Skipping: Dev auth already checked (Result: ${isDevAuthEnabled.value})`)
      return
    }
    
    // CRITICAL: Never enable dev auth in production builds
    if (isProduction.value) {
      console.log('🏭 Production Vite build detected → Dev auth force disabled')
      isDevAuthEnabled.value = false
      devAuthCheckComplete.value = true
      return
    }
    
    isChecking.value = true
    
    try {
      console.log(`🌐 Calling: ${API_BASE_URL}/api/auth/dev-status`)
      const response = await axios.get(`${API_BASE_URL}/api/auth/dev-status`, {
        timeout: 5000
      })
      
      console.log('📡 Backend response:', response.data)
      
      // Double-check that we're not in production
      if (isProduction.value) {
        console.warn('🚨 Production Vite build detected → Overriding backend response')
        isDevAuthEnabled.value = false
      } else {
        isDevAuthEnabled.value = response.data.dev_auth_enabled || false
        console.log(`✅ Dev auth status: ${isDevAuthEnabled.value ? 'ENABLED' : 'DISABLED'}`)
      }
      
      devAuthCheckComplete.value = true
    } catch (err) {
      console.warn('⚠️  Dev auth check failed → Defaulting to disabled')
      console.warn(`   Error: ${err.message}`)
      if (err.code === 'ECONNREFUSED') {
        console.warn('   Cause: Backend not running or wrong port')
      } else if (err.code === 'ENOTFOUND') {
        console.warn('   Cause: Invalid backend URL')
      } else if (err.response?.status === 404) {
        console.warn('   Cause: Dev auth endpoint not found (dev mode not enabled)')
      }
      isDevAuthEnabled.value = false
      devAuthCheckComplete.value = true
      // Clear sessionStorage on error
      sessionStorage.removeItem('dev_auth_enabled')
    } finally {
      isChecking.value = false
    }
  }
  
  return {
    isDevAuthEnabled,  // Return the ref directly, not wrapped in computed
    devAuthCheckComplete,
    isChecking,
    checkDevAuthStatus
  }
}