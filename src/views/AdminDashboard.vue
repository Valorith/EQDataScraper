<template>
  <div class="admin-dashboard">
    <div class="dashboard-header">
      <h1>Admin Dashboard</h1>
      <p class="subtitle">Manage users, monitor app performance, and control system settings</p>
    </div>

    <div class="dashboard-grid">
      <!-- User Management Card -->
      <div class="dashboard-card">
        <div class="card-header">
          <div class="card-icon">
            <i class="fas fa-users"></i>
          </div>
          <h2>User Management</h2>
        </div>
        <div class="card-content">
          <div class="stat-row">
            <span class="stat-label">Total Users</span>
            <span class="stat-value">{{ stats.users?.total || stats.totalUsers || 0 }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Active Today</span>
            <span class="stat-value">{{ stats.users?.active_today || stats.activeToday || 0 }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Admin Users</span>
            <span class="stat-value">{{ stats.users?.admins || stats.adminUsers || 0 }}</span>
          </div>
        </div>
        <div class="card-actions">
          <router-link to="/admin/users" class="action-button primary">
            <i class="fas fa-arrow-right"></i>
            Manage Users
          </router-link>
        </div>
      </div>

      <!-- Cache Management Card -->
      <div class="dashboard-card">
        <div class="card-header">
          <div class="card-icon cache">
            <i class="fas fa-database"></i>
          </div>
          <h2>Cache Management</h2>
        </div>
        <div class="card-content">
          <div class="stat-row">
            <span class="stat-label">Cache Status</span>
            <span class="stat-value" :class="cacheStatus.healthy ? 'success' : 'warning'">
              {{ cacheStatus.healthy ? 'Healthy' : 'Needs Attention' }}
            </span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Cached Classes</span>
            <span class="stat-value">{{ cacheStatus.cachedClasses || 0 }}/16</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Last Update</span>
            <span class="stat-value">{{ formatLastUpdate(cacheStatus.lastUpdate) }}</span>
          </div>
        </div>
        <div class="card-actions">
          <router-link to="/admin/cache" class="action-button primary">
            <i class="fas fa-arrow-right"></i>
            Manage Cache
          </router-link>
        </div>
      </div>

      <!-- Scraping Control Card -->
      <div class="dashboard-card">
        <div class="card-header">
          <div class="card-icon scraping">
            <i class="fas fa-sync-alt"></i>
          </div>
          <h2>Scraping Control</h2>
        </div>
        <div class="card-content">
          <div class="stat-row">
            <span class="stat-label">Status</span>
            <span class="stat-value" :class="scrapingStatus.active ? 'warning' : 'success'">
              {{ scrapingStatus.active ? 'In Progress' : 'Idle' }}
            </span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Current Class</span>
            <span class="stat-value">{{ scrapingStatus.currentClass || 'None' }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Progress</span>
            <span class="stat-value">{{ scrapingStatus.progress || 'N/A' }}</span>
          </div>
        </div>
        <div class="card-actions">
          <router-link to="/admin/scraping" class="action-button primary">
            <i class="fas fa-arrow-right"></i>
            Manage Scraping
          </router-link>
        </div>
      </div>

      <!-- System Health Card -->
      <div class="dashboard-card">
        <div class="card-header">
          <div class="card-icon health">
            <i class="fas fa-heartbeat"></i>
          </div>
          <h2>System Health</h2>
        </div>
        <div class="card-content">
          <div class="stat-row">
            <span class="stat-label">API Status</span>
            <span class="stat-value success">{{ systemHealth.apiStatus || 'Online' }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Response Time</span>
            <span class="stat-value">{{ systemHealth.avgResponseTime || 0 }}ms</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Error Rate</span>
            <span class="stat-value" :class="(systemHealth.errorRate || 0) > 5 ? 'warning' : 'success'">
              {{ systemHealth.errorRate || 0 }}%
            </span>
          </div>
        </div>
        <div class="card-actions">
          <router-link to="/admin/system" class="action-button primary">
            <i class="fas fa-arrow-right"></i>
            System Details
          </router-link>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions">
      <h2>Quick Actions</h2>
      <div class="action-grid">
        <button @click="refreshAllCaches" class="quick-action-btn" :disabled="refreshing">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': refreshing }"></i>
          <span>Refresh All Caches</span>
        </button>
        <button @click="triggerFullScrape" class="quick-action-btn" :disabled="scraping">
          <i class="fas fa-download" :class="{ 'fa-spin': scraping }"></i>
          <span>Full Data Scrape</span>
        </button>
        <button @click="exportData" class="quick-action-btn">
          <i class="fas fa-file-export"></i>
          <span>Export Data</span>
        </button>
        <button @click="viewLogs" class="quick-action-btn">
          <i class="fas fa-file-alt"></i>
          <span>View Logs</span>
        </button>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="recent-activity">
      <h2>Recent Activity</h2>
      <div class="activity-list">
        <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
          <div class="activity-icon" :class="activity.type">
            <i :class="getActivityIcon(activity.type)"></i>
          </div>
          <div class="activity-content">
            <p class="activity-description">{{ activity.description }}</p>
            <span class="activity-time">{{ formatTime(activity.timestamp) }}</span>
          </div>
        </div>
        <div v-if="recentActivities.length === 0" class="no-activity">
          <p>No recent activity to display</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()

// API base URL - in development, use empty string so proxy handles /api routes
const API_BASE_URL = import.meta.env.PROD ? 
  (import.meta.env.VITE_BACKEND_URL || 'https://eqdatascraper-backend-production.up.railway.app') : 
  ''

// State
const stats = ref({
  totalUsers: 0,
  activeToday: 0,
  adminUsers: 0
})

const cacheStatus = ref({
  healthy: true,
  cachedClasses: 0,
  lastUpdate: null
})

const scrapingStatus = ref({
  active: false,
  currentClass: null,
  progress: null
})

const systemHealth = ref({
  apiStatus: 'Online',
  avgResponseTime: 0,
  errorRate: 0
})

const recentActivities = ref([])
const refreshing = ref(false)
const scraping = ref(false)

let refreshInterval = null

// Methods
const loadDashboardData = async () => {
  
  // Load stats
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const statsRes = await axios.get(`${API_BASE_URL}/api/admin/stats`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    // Handle both success response formats
    if (statsRes.data.data) {
      stats.value = statsRes.data.data
    } else {
      stats.value = statsRes.data
    }
  } catch (error) {
    console.error('Error loading stats:', error)
    // Set default values
    stats.value = { totalUsers: 0, activeToday: 0, adminUsers: 0 }
  }

  // Load cache status
  try {
    const cacheRes = await axios.get(`${API_BASE_URL}/api/cache/status`)
    const cacheData = cacheRes.data
    cacheStatus.value = {
      healthy: cacheData.total_cached >= 10,
      cachedClasses: cacheData.total_cached,
      lastUpdate: cacheData.last_update
    }
  } catch (error) {
    console.error('Error loading cache status:', error)
    cacheStatus.value = { healthy: false, cachedClasses: 0, lastUpdate: null }
  }

  // Load health
  try {
    const healthRes = await axios.get(`${API_BASE_URL}/api/health`)
    systemHealth.value = healthRes.data
  } catch (error) {
    console.error('Error loading health:', error)
    systemHealth.value = { apiStatus: 'Unknown', avgResponseTime: 0, errorRate: 0 }
  }

  // Load activities
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const activitiesRes = await axios.get(`${API_BASE_URL}/api/admin/activities`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    // Handle both response formats
    if (activitiesRes.data.success && activitiesRes.data.data) {
      recentActivities.value = activitiesRes.data.data.activities || []
    } else if (activitiesRes.data.activities) {
      recentActivities.value = activitiesRes.data.activities
    } else {
      recentActivities.value = []
    }
  } catch (error) {
    console.error('Error loading activities:', error)
    recentActivities.value = []
  }
}

const refreshAllCaches = async () => {
  refreshing.value = true
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    await axios.post(`${API_BASE_URL}/api/cache/refresh`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    await loadDashboardData()
  } catch (error) {
    console.error('Error refreshing caches:', error)
  } finally {
    refreshing.value = false
  }
}

const triggerFullScrape = async () => {
  if (confirm('This will scrape all class data. This may take several minutes. Continue?')) {
    scraping.value = true
    try {
      const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
      await axios.post(`${API_BASE_URL}/api/scrape-all`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      await loadDashboardData()
    } catch (error) {
      console.error('Error triggering scrape:', error)
    } finally {
      scraping.value = false
    }
  }
}

const exportData = () => {
  router.push('/admin/export')
}

const viewLogs = () => {
  router.push('/admin/logs')
}

const formatLastUpdate = (timestamp) => {
  if (!timestamp) return 'Never'
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  const hours = Math.floor(diff / (1000 * 60 * 60))
  if (hours < 1) return 'Just now'
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / (1000 * 60))
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

const getActivityIcon = (type) => {
  const icons = {
    user_login: 'fas fa-sign-in-alt',
    user_register: 'fas fa-user-plus',
    cache_refresh: 'fas fa-sync-alt',
    scrape_complete: 'fas fa-check-circle',
    error: 'fas fa-exclamation-triangle',
    admin_action: 'fas fa-shield-alt'
  }
  return icons[type] || 'fas fa-info-circle'
}

// Lifecycle
onMounted(() => {
  loadDashboardData()
  // Refresh data every 30 seconds
  refreshInterval = setInterval(loadDashboardData, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

</script>

<style scoped>
@import '../style-constants.css';

.admin-dashboard {
  padding: 20px;
  padding-top: var(--header-height);
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  margin-bottom: 40px;
  margin-top: 20px; /* Add extra spacing from the top */
}

.dashboard-header h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: #666;
  font-size: 1.1rem;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 25px;
  margin-bottom: 40px;
}

.dashboard-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 25px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.dashboard-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.card-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 1.5rem;
}

.card-icon.cache {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.card-icon.scraping {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.card-icon.health {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
}

.card-header h2 {
  font-size: 1.3rem;
  margin: 0;
  color: #1a202c;
  font-weight: 600;
}

.card-content {
  margin-bottom: 20px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-label {
  color: #4a5568;
  font-size: 0.95rem;
  font-weight: 500;
}

.stat-value {
  font-weight: 700;
  font-size: 1.1rem;
  color: #1a202c;
}

.stat-value.success {
  color: #10b981;
}

.stat-value.warning {
  color: #f59e0b;
}

.card-actions {
  text-align: center;
}

.action-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.action-button:hover {
  transform: translateX(5px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.quick-actions {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 30px;
  margin-bottom: 40px;
}

.quick-actions h2 {
  margin-bottom: 20px;
  color: #1a202c;
  font-weight: 600;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.quick-action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.quick-action-btn:hover {
  border-color: #667eea;
  transform: translateY(-3px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.quick-action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.quick-action-btn i {
  font-size: 1.5rem;
  color: #667eea;
}

.quick-action-btn span {
  font-weight: 500;
  color: #1a202c;
}

.recent-activity {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 30px;
}

.recent-activity h2 {
  margin-bottom: 20px;
  color: #1a202c;
  font-weight: 600;
}

.activity-list {
  max-height: 400px;
  overflow-y: auto;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 15px 0;
  border-bottom: 1px solid #eee;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.activity-icon.user_login {
  background: #e0f2fe;
  color: #0284c7;
}

.activity-icon.user_register {
  background: #d1fae5;
  color: #059669;
}

.activity-icon.cache_refresh {
  background: #fef3c7;
  color: #d97706;
}

.activity-icon.error {
  background: #fee2e2;
  color: #dc2626;
}

.activity-content {
  flex: 1;
}

.activity-description {
  margin: 0 0 5px 0;
  font-weight: 500;
  color: #1a202c;
}

.activity-time {
  color: #4a5568;
  font-size: 0.85rem;
}

.no-activity {
  text-align: center;
  padding: 40px;
  color: #4a5568;
}

@media (max-width: 768px) {
  .dashboard-header h1 {
    font-size: 2rem;
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .action-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>