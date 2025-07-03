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

// Optimized initialization: backend now preloads data on startup
console.log('🚀 Starting EQDataScraper initialization...')

spellsStore.warmupBackend()
  .then(success => {
    if (success) {
      console.log('✅ Backend connection established!')
      console.log('🏃‍♂️ Backend has preloaded spell data on startup - checking server memory status...')
      
      // Start cache pre-hydration but with faster expectation since server has data ready
      return spellsStore.preHydrateCache()
    } else {
      console.log('⚠️ Backend warmup failed, app will use on-demand loading')
      return Promise.resolve(false)
    }
  })
  .then(hydrationSuccess => {
    if (hydrationSuccess) {
      console.log('🎉 Cache pre-hydration complete! Server memory optimization enabled.')
      console.log('⚡ All classes ready for instant loading from server memory!')
    } else {
      console.log('📱 App ready with on-demand loading. Classes will load when clicked.')
    }
  })
  .catch(error => {
    console.warn('🔄 Initialization encountered issues, falling back to on-demand loading:', error.message)
  }) 