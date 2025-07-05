<template>
  <div class="admin-dashboard-test">
    <h1>Admin Dashboard Test</h1>
    <p>If you can see this, the route is working!</p>
    <p>User: {{ userEmail }}</p>
    <p>Role: {{ userRole }}</p>
  </div>
</template>

<script setup>
import { useUserStore } from '../stores/userStore'

console.log('🧪 AdminDashboardTest loading...')

const userStore = useUserStore()
const userEmail = userStore.user?.email || 'Not loaded'
const userRole = userStore.user?.role || 'Not loaded'

console.log('🧪 Test component loaded successfully')
</script>

<style scoped>
.admin-dashboard-test {
  padding: 20px;
}
</style>