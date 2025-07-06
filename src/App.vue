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
    
    <!-- Dev Login Panel (only shows in development with flag) -->
    <DevLogin v-if="!isProduction" />
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

export default {
  name: 'App',
  components: {
    DebugPanel,
    DevLogin,
    AppLogo,
    GoogleAuthButton,
    UserMenu
  },
  setup() {
    const spellsStore = useSpellsStore()
    const userStore = useUserStore()
    const isProduction = import.meta.env.PROD
    return { spellsStore, userStore, isProduction }
  },
  methods: {
    toggleDebugPanel() {
      if (this.$refs.debugPanel) {
        this.$refs.debugPanel.toggleDebugPanel()
      }
    }
  },
  async mounted() {
    // Import clearAuth utility for debugging
    import('@/utils/clearAuth.js')
    
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