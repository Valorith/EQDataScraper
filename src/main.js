import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './style.css'
import { useSpellsStore } from './stores/spells'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Warmup backend connection as soon as the app is ready
app.mount('#app')

// Initialize store and warmup backend after mounting
const spellsStore = useSpellsStore()

// Sequential initialization: warmup first, then pre-hydrate cache
spellsStore.warmupBackend()
  .then(success => {
    if (success) {
      // Start cache pre-hydration in background (non-blocking)
      spellsStore.preHydrateCache().catch(error => {
        console.warn('Cache pre-hydration failed, will load on demand:', error)
      })
    }
  })
  .catch(error => {
    console.warn('Initial backend warmup failed, will retry on first request:', error)
  }) 