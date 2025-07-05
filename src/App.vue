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
    
    <router-view @toggle-debug-panel="toggleDebugPanel" />
    
    <!-- Debug Panel for production debugging -->
    <DebugPanel ref="debugPanel" />
  </div>
</template>

<script>
import { useSpellsStore } from './stores/spells'
import { useUserStore } from './stores/userStore'
import DebugPanel from './components/DebugPanel.vue'
import AppLogo from './components/AppLogo.vue'
import GoogleAuthButton from './components/GoogleAuthButton.vue'
import UserMenu from './components/UserMenu.vue'

export default {
  name: 'App',
  components: {
    DebugPanel,
    AppLogo,
    GoogleAuthButton,
    UserMenu
  },
  setup() {
    const spellsStore = useSpellsStore()
    const userStore = useUserStore()
    return { spellsStore, userStore }
  },
  methods: {
    toggleDebugPanel() {
      if (this.$refs.debugPanel) {
        this.$refs.debugPanel.toggleDebugPanel()
      }
    }
  },
  async mounted() {
    console.log('🔧 Environment Variables Debug v4:')
    console.log('VITE_BACKEND_URL:', import.meta.env.VITE_BACKEND_URL)
    console.log('import.meta.env.PROD:', import.meta.env.PROD)
    console.log('All Vite env vars:', import.meta.env)
    
    // Test the fallback logic directly
    const API_BASE_URL = (() => {
      // In production, only use VITE_BACKEND_URL if it's a valid production URL
      if (import.meta.env.PROD) {
        const envUrl = import.meta.env.VITE_BACKEND_URL
        // Only use env URL if it's a valid production URL (not localhost)
        if (envUrl && !envUrl.includes('localhost') && !envUrl.includes('127.0.0.1')) {
          return envUrl
        }
        // Default production backend URL
        return 'https://eqdatascraper-backend-production.up.railway.app'
      }
      
      // In development, use env variable or default to localhost
      return import.meta.env.VITE_BACKEND_URL || 'http://localhost:5001'
    })()
    console.log('Computed API_BASE_URL:', API_BASE_URL)
    console.log('Build timestamp:', new Date().toISOString())
    
    // Initialize authentication system
    try {
      console.log('🔐 Initializing authentication...')
      await this.userStore.initializeAuth()
      this.userStore.setupTokenRefresh()
      console.log('✅ Authentication initialized')
    } catch (error) {
      console.error('❌ Authentication initialization failed:', error)
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
</style> 