<template>
  <div id="app" class="railway-deployment-debug">
    <!-- App Logo - appears on all pages -->
    <AppLogo />
    
    <!-- User Authentication (top-right corner) -->
    <div class="auth-section">
      <UserMenu v-if="userStore.isAuthenticated" />
      <GoogleAuthButton v-else @trigger-dev-login="handleTriggerDevLogin" />
    </div>
    
    <!-- Cache pre-hydration indicator -->
    <div v-if="spellsStore.isPreHydrating" class="cache-prehydration-indicator">
      <div class="prehydration-content">
        <div class="prehydration-spinner"></div>
        <span>Updating cache & loading spell data... ({{ spellsStore.preHydrationProgress.loaded }}/{{ spellsStore.preHydrationProgress.total }})</span>
      </div>
    </div>
    
    <router-view />
    
    
    <!-- Dev Login Panel (only in development mode) -->
    <DevLogin v-show="showDevLogin" ref="devLogin" :debug-panel-visible="false" />
    
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
import { useSpellsStore } from './stores/spells'
import { useUserStore } from './stores/userStore'
import DevLogin from './components/DevLogin.vue'
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
    DevLogin,
    AppLogo,
    GoogleAuthButton,
    UserMenu,
    ToastNotification
  },
  setup() {
    const spellsStore = useSpellsStore()
    const userStore = useUserStore()
    const isProduction = import.meta.env.PROD
    const currentToast = ref(null)
    const toast = ref(null)
    const devMode = useDevMode()
    const devLogin = ref(null)
    
    // Use the ref directly from the composable
    const { isDevAuthEnabled, checkDevAuthStatus } = devMode
    
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
    
    
    const showDevLogin = computed(() => {
      // Check custom app mode from run.py
      const appMode = import.meta.env.VITE_APP_MODE
      
      // Only show dev login in development mode
      if (appMode !== 'development') {
        return false
      }
      
      // Only show when backend dev auth is explicitly enabled via run.py start dev
      const backendEnabled = isDevAuthEnabled.value
      const result = backendEnabled
      console.log(`🔧 Dev Login Panel: ${result ? 'VISIBLE' : 'HIDDEN'} (App Mode: ${appMode}, Backend Auth: ${backendEnabled})`)
      return result
    })
    
    const handleTriggerDevLogin = () => {
      console.log('🔧 Opening dev login panel...')
      if (devLogin.value && devLogin.value.toggleMinimize) {
        devLogin.value.toggleMinimize()
        console.log('✅ Dev login panel opened successfully')
      } else {
        console.error('❌ Failed to open dev login panel - component not found')
      }
    }

    return { 
      spellsStore, 
      userStore, 
      isProduction, 
      currentToast, 
      toast, 
      isDevAuthEnabled, 
      checkDevAuthStatus,
      showDevLogin,
      devLogin,
      handleTriggerDevLogin
    }
  },
  methods: {
  },
  async mounted() {
    // Import clearAuth utility for debugging
    import('@/utils/clearAuth.js')
    
    // Log current environment status
    console.log('🏁 App starting...')
    console.log(`🏁 Production build: ${this.isProduction}`)
    console.log(`🏁 Vite mode: ${import.meta.env.MODE}`)
    console.log(`🏁 Should check dev auth: ${!this.isProduction}`)
    
    // Always check dev auth status (backend controls if it's enabled)
    // Try immediate check first
    await this.checkDevAuthStatus()
    
    // Log final dev auth state
    console.log(`🏁 Final dev auth enabled:`, this.isDevAuthEnabled)
    
    // If failed, retry after a delay for backend startup
    if (!this.isDevAuthEnabled && !this.isProduction) {
      console.debug('🔧 Dev auth check failed, retrying in 3 seconds...')
      setTimeout(async () => {
        await this.checkDevAuthStatus(true) // Force re-check
        console.log(`🏁 Retry result - dev auth enabled:`, this.isDevAuthEnabled)
      }, 3000)
    }
    
    // Initialize authentication system
    try {
      if (import.meta.env.MODE === 'development') {
        console.debug('🔐 Initializing authentication...')
      }
      
      // The userStore.initializeAuth() now handles all OAuth state cleanup
      // and has proper timeouts to prevent hanging
      await this.userStore.initializeAuth()
      this.userStore.setupTokenRefresh()
      
      if (import.meta.env.MODE === 'development') {
        console.debug('✅ Authentication initialized')
      }
    } catch (error) {
      console.error('❌ Authentication initialization failed:', error)
      // Ensure loading state is reset on error
      this.userStore.isLoading = false
    }
    
    // Skip cache initialization in App.vue since main.js already handles it
    // This prevents duplicate initialization attempts and 429 errors
    if (import.meta.env.MODE === 'development') {
      console.debug('🎯 Cache initialization handled by main.js')
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