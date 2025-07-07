<template>
  <div id="app" class="railway-deployment-debug">
    <!-- App Logo - appears on all pages -->
    <AppLogo />
    
    <!-- User Authentication (top-right corner) -->
    <div class="auth-section">
      <UserMenu v-if="userStore.isAuthenticated" />
      <GoogleAuthButton v-else />
    </div>
    
    <!-- Cache pre-hydration indicator -->
    <div v-if="spellsStore.isPreHydrating" class="cache-prehydration-indicator">
      <div class="prehydration-content">
        <div class="prehydration-spinner"></div>
        <span>Updating cache & loading spell data... ({{ spellsStore.preHydrationProgress.loaded }}/{{ spellsStore.preHydrationProgress.total }})</span>
      </div>
    </div>
    
    <router-view />
    
    <!-- Debug Panel for production debugging -->
    <DebugPanel ref="debugPanel" />
    
    <!-- Dev Login Panel (only shows in development with flag) -->
    <DevLogin v-if="!isProduction" ref="devLogin" />
    
    <!-- Toast Notification -->
    <ToastNotification 
      v-if="currentToast"
      ref="toast"
      :key="currentToast.id"
      :message="currentToast.message"
      :type="currentToast.type"
      :duration="currentToast.duration"
    />
    
    <!-- Debug Panel Toggle Button -->
    <button 
      v-if="!isProduction || debugPanelEnabled" 
      @click="toggleDebugPanel" 
      class="debug-toggle-btn"
      :class="{ 'active': debugPanelVisible }"
      title="Toggle Debug Panel"
    >
      🔧
    </button>
    
    <!-- Dev Login Toggle Button (for simulating login) -->
    <button 
      v-if="!isProduction" 
      @click="toggleDevLogin" 
      class="dev-login-toggle-btn"
      title="Toggle Dev Login Panel"
    >
      👤
    </button>
  </div>
</template>

<script>
import { useSpellsStore } from './stores/spells'
import { useUserStore } from './stores/userStore'
import DebugPanel from './components/DebugPanel.vue'
import DevLogin from './components/DevLogin.vue'
import AppLogo from './components/AppLogo.vue'
import GoogleAuthButton from './components/GoogleAuthButton.vue'
import UserMenu from './components/UserMenu.vue'
import ToastNotification from './components/ToastNotification.vue'
import { toastService } from './services/toastService'
import { ref, watch } from 'vue'

export default {
  name: 'App',
  components: {
    DebugPanel,
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
    
    return { spellsStore, userStore, isProduction, currentToast, toast }
  },
  computed: {
    debugPanelEnabled() {
      // Check if debug panel is enabled via localStorage (for production)
      return localStorage.getItem('debug-panel') === 'true'
    },
    debugPanelVisible() {
      // Check if debug panel is currently visible
      return this.$refs.debugPanel?.showDebugPanel || false
    },
    isAdminRoute() {
      // Check if current route is an admin route
      return this.$route?.path?.startsWith('/admin')
    }
  },
  methods: {
    toggleDebugPanel() {
      if (this.$refs.debugPanel) {
        this.$refs.debugPanel.toggleDebugPanel()
      }
    },
    toggleDevLogin() {
      if (this.$refs.devLogin && typeof this.$refs.devLogin.toggleMinimize === 'function') {
        this.$refs.devLogin.toggleMinimize()
      } else {
        console.debug('DevLogin component not available or toggleMinimize method not found')
      }
    }
  },
  async mounted() {
    // Import clearAuth utility for debugging
    import('@/utils/clearAuth.js')
    
    // Initialize authentication system
    try {
      console.log('🔐 Initializing authentication...')
      
      // The userStore.initializeAuth() now handles all OAuth state cleanup
      // and has proper timeouts to prevent hanging
      await this.userStore.initializeAuth()
      this.userStore.setupTokenRefresh()
      console.log('✅ Authentication initialized')
    } catch (error) {
      console.error('❌ Authentication initialization failed:', error)
      // Ensure loading state is reset on error
      this.userStore.isLoading = false
    }
    
    // Skip cache initialization in App.vue since main.js already handles it
    // This prevents duplicate initialization attempts and 429 errors
    console.log('🎯 Cache initialization handled by main.js')
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

/* Debug Panel Toggle Button */
.debug-toggle-btn {
  position: fixed;
  bottom: 20px;
  right: 80px; /* Position next to cache indicator */
  width: 48px;
  height: 48px;
  background: linear-gradient(145deg, rgba(147, 112, 219, 0.2), rgba(147, 112, 219, 0.1));
  backdrop-filter: blur(15px);
  border: 2px solid rgba(147, 112, 219, 0.3);
  border-radius: 12px;
  color: white;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 9998; /* Below cache indicator */
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.debug-toggle-btn:hover {
  background: linear-gradient(145deg, rgba(147, 112, 219, 0.4), rgba(147, 112, 219, 0.2));
  border-color: rgba(147, 112, 219, 0.6);
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(147, 112, 219, 0.4);
}

.debug-toggle-btn.active {
  background: linear-gradient(145deg, rgba(147, 112, 219, 0.6), rgba(147, 112, 219, 0.4));
  border-color: rgba(147, 112, 219, 0.8);
  box-shadow: 0 0 20px rgba(147, 112, 219, 0.6);
  animation: debugPulse 2s infinite;
}

@keyframes debugPulse {
  0%, 100% {
    box-shadow: 0 0 20px rgba(147, 112, 219, 0.6);
  }
  50% {
    box-shadow: 0 0 30px rgba(147, 112, 219, 0.8), 0 0 40px rgba(147, 112, 219, 0.4);
  }
}

/* Dev Login Toggle Button */
.dev-login-toggle-btn {
  position: fixed;
  bottom: 20px;
  right: 20px; /* Far right corner */
  width: 48px;
  height: 48px;
  background: linear-gradient(145deg, rgba(72, 187, 120, 0.2), rgba(72, 187, 120, 0.1));
  backdrop-filter: blur(15px);
  border: 2px solid rgba(72, 187, 120, 0.3);
  border-radius: 12px;
  color: white;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 9997; /* Below debug toggle */
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.dev-login-toggle-btn:hover {
  background: linear-gradient(145deg, rgba(72, 187, 120, 0.4), rgba(72, 187, 120, 0.2));
  border-color: rgba(72, 187, 120, 0.6);
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(72, 187, 120, 0.4);
}
</style> 