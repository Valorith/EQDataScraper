<template>
  <div id="app" class="railway-deployment-debug">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App',
  mounted() {
    console.log('🔧 Environment Variables Debug v2:')
    console.log('VITE_BACKEND_URL:', import.meta.env.VITE_BACKEND_URL)
    console.log('All Vite env vars:', import.meta.env)
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