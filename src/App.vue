<template>
  <div id="app" class="railway-deployment-debug">
    <!-- Cache pre-hydration indicator -->
    <div v-if="spellsStore.isPreHydrating" class="cache-prehydration-indicator">
      <div class="prehydration-content">
        <div class="prehydration-spinner"></div>
        <span>Updating cache & loading spell data... ({{ spellsStore.preHydrationProgress.loaded }}/{{ spellsStore.preHydrationProgress.total }})</span>
      </div>
    </div>
    
    <router-view />
    
    <!-- Debug Panel for production debugging -->
    <DebugPanel />
  </div>
</template>

<script>
import { useSpellsStore } from './stores/spells'
import DebugPanel from './components/DebugPanel.vue'

export default {
  name: 'App',
  components: {
    DebugPanel
  },
  setup() {
    const spellsStore = useSpellsStore()
    return { spellsStore }
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
    
    // Initialize cache system
    try {
      console.log('🚀 Initializing cache system...')
      
      // Start backend warmup and cache pre-hydration in parallel
      const [warmupResult, preHydrationResult] = await Promise.allSettled([
        this.spellsStore.warmupBackend(),
        this.spellsStore.preHydrateCache()
      ])
      
      console.log('Warmup result:', warmupResult.status === 'fulfilled' ? warmupResult.value : warmupResult.reason)
      console.log('Pre-hydration result:', preHydrationResult.status === 'fulfilled' ? preHydrationResult.value : preHydrationResult.reason)
      
      if (warmupResult.status === 'fulfilled' && warmupResult.value) {
        console.log('✅ Backend is warmed up and ready')
      } else {
        console.warn('⚠️ Backend warmup failed, but application will continue with on-demand loading')
      }
      
    } catch (error) {
      console.error('❌ Cache initialization failed:', error)
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