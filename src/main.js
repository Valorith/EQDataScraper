import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import router from './router'
import App from './App.vue'
import './style.css'
import './utils/authInterceptor' // Import auth interceptor for token handling (must be first)
import './utils/axiosConfig' // Import axios configuration
// DISABLED: Spell system temporarily disabled for redesign
// import { useSpellsStore } from './stores/spells'

const app = createApp(App)
const pinia = createPinia()

// Add persistence plugin for user authentication state
pinia.use(piniaPluginPersistedstate)

app.use(pinia)
app.use(router)

// Warmup backend connection as soon as the app is ready
app.mount('#app')

// DISABLED: Spell system temporarily disabled for redesign
// Initialize store after mounting
// const spellsStore = useSpellsStore()

// Simple initialization - just check if backend is available
if (import.meta.env.MODE === 'development') {
  console.log('🚀 EQDataScraper initialized')
}

// DISABLED: Spell system temporarily disabled for redesign
// Single warmup call to check backend availability
// spellsStore.warmupBackend()
//   .then(success => {
//     if (success) {
//       console.log('✅ Backend connection established')
//     } else {
//       // Only show warning in development mode
//       if (import.meta.env.MODE === 'development') {
//         console.debug('⚠️ Backend not available, will connect on demand')
//       }
//     }
//   })
//   .catch(error => {
//     // Silently handle all errors - warmupBackend already logs if needed
//   }) 