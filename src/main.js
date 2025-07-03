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

// Resilient initialization: try warmup and pre-hydration, but don't block the app
console.log('🚀 Starting EQDataScraper initialization...')

spellsStore.warmupBackend()
  .then(success => {
    if (success) {
      console.log('✅ Backend connection established, starting cache pre-hydration...')
      // Start cache pre-hydration in background (non-blocking)
      return spellsStore.preHydrateCache()
    } else {
      console.log('⚠️ Backend warmup failed, app will use on-demand loading')
      return Promise.resolve(false)
    }
  })
  .then(hydrationSuccess => {
    if (hydrationSuccess) {
      console.log('🎉 Cache pre-hydration complete! All classes ready for instant loading.')
    } else {
      console.log('📱 App ready with on-demand loading. Classes will load when clicked.')
    }
  })
  .catch(error => {
    console.warn('🔄 Initialization encountered issues, falling back to on-demand loading:', error.message)
  }) 