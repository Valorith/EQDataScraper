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
spellsStore.warmupBackend().catch(error => {
  console.warn('Initial backend warmup failed, will retry on first request:', error)
}) 