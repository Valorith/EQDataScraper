<template>
  <div id="app" class="railway-deployment-debug">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App',
  mounted() {
    console.log('🔧 Environment Variables Debug v3:')
    console.log('VITE_BACKEND_URL:', import.meta.env.VITE_BACKEND_URL)
    console.log('import.meta.env.PROD:', import.meta.env.PROD)
    console.log('All Vite env vars:', import.meta.env)
    
    // Test the fallback logic directly
    const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 
      (import.meta.env.PROD ? 'https://eqdatascraper-backend-production.up.railway.app' : '')
    console.log('Computed API_BASE_URL:', API_BASE_URL)
    console.log('Build timestamp:', new Date().toISOString())
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
</style> 