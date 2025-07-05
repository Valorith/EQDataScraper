import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import router from './router'
import App from './App.vue'
import './style.css'
import { useSpellsStore } from './stores/spells'

const app = createApp(App)
const pinia = createPinia()

// Add persistence plugin for user authentication state
pinia.use(piniaPluginPersistedstate)

app.use(pinia)
app.use(router)

// Warmup backend connection as soon as the app is ready
app.mount('#app')

// Initialize store after mounting
const spellsStore = useSpellsStore()

// Simple initialization - just check if backend is available
console.log('🚀 EQDataScraper initialized')

// Single warmup call to check backend availability
spellsStore.warmupBackend()
  .then(success => {
    if (success) {
      console.log('✅ Backend connection established')
    } else {
      console.log('⚠️ Backend connection failed, will retry on demand')
    }
  })
  .catch(error => {
    // Silently handle errors to avoid console spam
    if (error.response?.status !== 429) {
      console.warn('Backend check failed:', error.message)
    }
  }) 