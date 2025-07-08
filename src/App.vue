<template>
  <div id="app" class="railway-deployment-debug">
    <!-- App Logo - appears on all pages -->
    <AppLogo />
    
    <!-- User Authentication (top-right corner) -->
    <div class="auth-section">
      <UserMenu v-if="userStore.isAuthenticated" />
      <div v-else-if="isDevModeBypass" class="dev-bypass-indicator">
        <span class="dev-badge">DEV MODE</span>
        <span class="dev-user">Admin User</span>
      </div>
      <GoogleAuthButton v-else />
    </div>
    
    <!-- Cache pre-hydration indicator - DISABLED -->
    <!-- Spell system temporarily disabled for redesign -->
    
    <router-view />
    
    
    <!-- Dev Login Panel - REMOVED: No longer needed with dev mode bypass -->
    
    <!-- Toast Notification -->
    <ToastNotification 
      v-if="currentToast"
      ref="toast"
      :key="currentToast.id"
      :message="currentToast.message"
      :type="currentToast.type"
      :duration="currentToast.duration"
    />
  </div>
</template>

<script>
// DISABLED: Spell system temporarily disabled for redesign
// import { useSpellsStore } from './stores/spells'
import { useUserStore } from './stores/userStore'
// import DevLogin from './components/DevLogin.vue' // REMOVED: No longer needed
import AppLogo from './components/AppLogo.vue'
import GoogleAuthButton from './components/GoogleAuthButton.vue'
import UserMenu from './components/UserMenu.vue'
import ToastNotification from './components/ToastNotification.vue'
import { toastService } from './services/toastService'
import { ref, watch, watchEffect, toRef, computed } from 'vue'
import { useDevMode } from './composables/useDevMode'

export default {
  name: 'App',
  components: {
    // DevLogin, // REMOVED: No longer needed with dev mode bypass
    AppLogo,
    GoogleAuthButton,
    UserMenu,
    ToastNotification
  },
  setup() {
    // DISABLED: Spell system temporarily disabled for redesign
    // const spellsStore = useSpellsStore()
    const userStore = useUserStore()
    const isProduction = import.meta.env.PROD
    const currentToast = ref(null)
    const toast = ref(null)
    const devMode = useDevMode()
    // Use the ref directly from the composable
    const { isDevAuthEnabled, checkDevAuthStatus } = devMode
    
    // Check if we should bypass auth completely in development mode
    const isDevModeBypass = computed(() => {
      // Use our custom dev auth flag set by run.py start dev
      return isDevAuthEnabled.value === true
    })
    
    // Watch for toast changes
    watch(() => toastService.getCurrent(), (newToast) => {
      currentToast.value = newToast
      if (newToast && toast.value) {
        // Use nextTick to ensure component is rendered
        import('vue').then(({ nextTick }) => {
          nextTick(() => {
            if (toast.value) {
              toast.value.show()
            }
          })
        })
      }
    }, { immediate: true })
    
    
    // showDevLogin and handleTriggerDevLogin REMOVED: No longer needed with dev mode bypass

    return { 
      // DISABLED: spellsStore disabled - spell system temporarily disabled
      userStore, 
      isProduction, 
      currentToast, 
      toast, 
      isDevAuthEnabled, 
      checkDevAuthStatus,
      isDevModeBypass
    }
  },
  methods: {
    // Method to manually refresh dev mode state (useful for debugging)
    async refreshDevMode() {
      const { refreshDevModeStatus } = useDevMode()
      await refreshDevModeStatus()
      if (import.meta.env.MODE === 'development') {
        console.log('🔄 Dev mode state refreshed')
      }
    }
  },
  async mounted() {
    // Import clearAuth utility for debugging
    import('@/utils/clearAuth.js')
    
    // Hot reload detection
    const isHotReload = window._appMountCount > 0
    window._appMountCount = (window._appMountCount || 0) + 1
    
    // Log current environment status (minimal logging)
    if (import.meta.env.MODE === 'development' && !isHotReload) {
      console.log(`🏁 App starting... ${isHotReload ? '(🔥 Hot Reload)' : '(Fresh)'}`)
    }
    
    // EARLY: Check and clear invalid dev auth state before checking bypass
    const appMode = import.meta.env.VITE_APP_MODE || 'undefined'
    if (appMode !== 'development' && this.isDevAuthEnabled) {
      if (import.meta.env.MODE === 'development') {
        console.log('🧹 Clearing invalid dev auth state on app mount')
      }
      this.isDevAuthEnabled = false
      sessionStorage.removeItem('dev_auth_enabled')
    }
    
    // EARLY: Set up dev mode bypass - completely skip auth in development mode
    if (this.isDevModeBypass) {
      if (import.meta.env.MODE === 'development') {
        console.log('🔧 Dev mode bypass enabled - setting up mock auth state')
      }
      this.userStore.user = {
        id: 1,
        email: 'dev@localhost.dev',
        first_name: 'Dev',
        last_name: 'Admin',
        role: 'admin',
        display_name: 'Dev Admin',
        anonymous_mode: false,
        avatar_class: null,
        avatar_url: 'https://ui-avatars.com/api/?name=Dev+Admin&background=667eea&color=fff',
        is_active: true,
        google_id: 'dev_bypass_user'
      }
      this.userStore.accessToken = 'dev_bypass_token'
      this.userStore.refreshToken = 'dev_bypass_refresh'
      this.userStore.isAuthenticated = true
      this.userStore.preferences = {
        default_class: null,
        theme_preference: 'auto',
        results_per_page: 20
      }
      if (import.meta.env.MODE === 'development') {
        console.log('🔧 Dev mode bypass setup complete - skipping all auth initialization')
      }
      return // Skip all other auth initialization
    }
    
    // For hot reloads, try to use existing state first
    const wasRestored = sessionStorage.getItem('dev_auth_enabled')
    const lastCheck = sessionStorage.getItem('dev_auth_last_check')
    const timeSinceLastCheck = lastCheck ? Date.now() - parseInt(lastCheck) : Infinity
    
    // Skip dev auth check on hot reload if recently checked (within 30 seconds)
    if (isHotReload && wasRestored && timeSinceLastCheck < 30000) {
      // Silently use cached state on hot reload
      
      // Ensure the dev auth state is properly restored
      if (window._devModeState) {
        window._devModeState.isDevAuthEnabled.value = wasRestored === 'true'
        window._devModeState.devAuthCheckComplete.value = true
        // State restored from sessionStorage on hot reload
      }
    } else if (!wasRestored || timeSinceLastCheck > 30000) {
      try {
        await this.checkDevAuthStatus()
      } catch (error) {
        // Dev auth check failed, using fallback
        // On error, try to use cached state as fallback
        if (wasRestored && window._devModeState) {
          window._devModeState.isDevAuthEnabled.value = wasRestored === 'true'
          window._devModeState.devAuthCheckComplete.value = true
        }
      }
    } else {
      // Using cached dev auth state
      
      // Ensure state consistency even for non-hot-reload scenarios
      if (window._devModeState && wasRestored) {
        window._devModeState.isDevAuthEnabled.value = wasRestored === 'true'
        window._devModeState.devAuthCheckComplete.value = true
      }
    }
    
    // Dev auth state initialized
    
    // Only retry if we didn't have cached state AND we're not in production AND not enabled
    if (!isHotReload && !wasRestored && !this.isDevAuthEnabled && !this.isProduction) {
      setTimeout(async () => {
        await this.checkDevAuthStatus(true) // Force re-check
      }, 3000)
    }
    
    // Initialize authentication system (skip on hot reload if already authenticated)
    try {
      const skipAuthInit = isHotReload && this.userStore.isAuthenticated
      
      if (skipAuthInit) {
        // Hot reload detected - skipping auth re-initialization
      } else {
        // Initializing authentication...
        
        // The userStore.initializeAuth() now handles all OAuth state cleanup
        // and has proper timeouts to prevent hanging
        await this.userStore.initializeAuth()
        this.userStore.setupTokenRefresh()
        
        // Authentication initialized
      }
    } catch (error) {
      console.error('❌ Authentication initialization failed:', error)
      // Ensure loading state is reset on error
      this.userStore.isLoading = false
    }
    
    // Skip cache initialization in App.vue since main.js already handles it
    // This prevents duplicate initialization attempts and 429 errors
    
    // Hot reload cleanup registration
    if (import.meta.hot) {
      import.meta.hot.dispose(() => {
        // App component disposing - preserving dev state
        // Preserve the current state in sessionStorage for hot reload
        if (window._devModeState) {
          sessionStorage.setItem('dev_auth_enabled', String(window._devModeState.isDevAuthEnabled.value))
          sessionStorage.setItem('dev_auth_check_complete', String(window._devModeState.devAuthCheckComplete.value))
          sessionStorage.setItem('dev_auth_last_check', String(window._devModeState.lastCheckTime))
        }
        
        // Save dev login state for hot reload persistence
        if (this.userStore.isAuthenticated) {
          this.userStore.saveDevLoginState()
        }
      })
      
      // Force re-evaluation of dev mode state after hot reload
      import.meta.hot.accept(() => {
        // App component hot reloaded - restoring dev state
        setTimeout(() => {
          if (window._devModeState) {
            const storedDevAuth = sessionStorage.getItem('dev_auth_enabled')
            if (storedDevAuth) {
              window._devModeState.isDevAuthEnabled.value = storedDevAuth === 'true'
              window._devModeState.devAuthCheckComplete.value = true
              // Dev mode state restored
            }
          }
        }, 100)
      })
    }
  }
}
</script>

<style>
#app {
  font-family: 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
  position: relative;
}

/* Authentication section positioning */
.auth-section {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1100; /* Higher than other elements to prevent overlap */
}

/* Dev bypass indicator styling */
.dev-bypass-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.3);
  border-radius: 8px;
  padding: 8px 16px;
  backdrop-filter: blur(10px);
}

.dev-badge {
  background: #ff6b6b;
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.dev-user {
  color: #f7fafc;
  font-size: 14px;
  font-weight: 500;
}

/* Cache pre-hydration indicator */
.cache-prehydration-indicator {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  color: #fff;
  padding: 12px 16px;
  border-radius: 8px;
  z-index: 9999;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  animation: slideInUp 0.3s ease-out;
}

.prehydration-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.prehydration-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes slideInUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

</style> 