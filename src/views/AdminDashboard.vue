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
          <i class="fas fa-cloud-download-alt" :class="{ 'fa-spin': scraping }"></i>
          <span>Full Data Scrape</span>
        </button>
        <button @click="exportData" class="quick-action-btn">
          <i class="fas fa-file-export"></i>
          <span>Export Data</span>
        </button>
        <button @click="viewLogs" class="quick-action-btn">
          <i class="fas fa-history"></i>
          <span>View Logs</span>
        </button>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="recent-activity">
      <h2>Recent Activity</h2>
      <div class="activity-list">
        <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
          <div v-if="isUserActivity(activity.type) && activity.userAvatar" class="activity-avatar">
            <img :src="activity.userAvatar" :alt="activity.userName || 'User'" />
          </div>
          <div v-else class="activity-icon" :class="activity.type">
            <i :class="getActivityIcon(activity.type)"></i>
          </div>
          <div class="activity-content">
            <p class="activity-description">{{ activity.description }}</p>
            <span class="activity-time">{{ formatTime(activity.timestamp) }}</span>
          </div>
        </div>
        <div v-if="recentActivities.length === 0" class="no-activity">
          <p>No activity logged yet</p>
          <p class="activity-help">Activity will appear here when users log in, search spells, or perform admin actions</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import { API_BASE_URL, buildApiUrl, API_ENDPOINTS } from '../config/api'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()

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
let activityRefreshInterval = null

// Methods
const loadDashboardData = async () => {
  console.log('Loading dashboard data...')
  
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
    if (error.response?.status === 401) {
      console.warn('Authentication issue loading stats')
    } else if (error.response?.status !== undefined) {
      console.error('Error loading stats:', error.response.status)
    }
    // Set default values
    stats.value = { totalUsers: 0, activeToday: 0, adminUsers: 0 }
  }

  // Load cache status
  try {
    // Try to get detailed cache status first
    const detailsRes = await axios.get(`${API_BASE_URL}/api/cache-status`)
    
    // Calculate total cached classes from the details
    let totalCached = 0
    let lastUpdate = null
    let mostRecentUpdate = null
    
    for (const [className, classData] of Object.entries(detailsRes.data)) {
      if (className !== '_config' && classData.cached) {
        totalCached++
        // Find the most recent update time - check multiple possible field names
        const updateTimeField = classData.last_updated || classData.cache_time || classData.lastUpdated
        if (updateTimeField) {
          const updateTime = new Date(updateTimeField)
          if (!mostRecentUpdate || updateTime > mostRecentUpdate) {
            mostRecentUpdate = updateTime
            lastUpdate = updateTimeField
          }
        }
      }
    }
    
    // If all classes are cached but no update time found, use current time
    if (totalCached > 0 && !lastUpdate) {
      lastUpdate = new Date().toISOString()
    }
    
    cacheStatus.value = {
      healthy: totalCached >= 10,
      cachedClasses: totalCached,
      lastUpdate: lastUpdate
    }
    
    console.log('Cache status from details:', { totalCached, lastUpdate })
    
    // Also try the summary endpoint for additional info
    try {
      const summaryRes = await axios.get(`${API_BASE_URL}/api/cache/status`)
      console.log('Cache summary response:', summaryRes.data)
      if (summaryRes.data.total_cached !== undefined) {
        // Use the summary data if it has more info
        cacheStatus.value.cachedClasses = summaryRes.data.total_cached
        if (summaryRes.data.last_update) {
          cacheStatus.value.lastUpdate = summaryRes.data.last_update
        }
      }
    } catch (e) {
      // Summary endpoint might not exist, that's ok
      console.log('Summary endpoint not available')
    }
  } catch (error) {
    console.error('Error loading cache status:', error)
    
    // Fallback: try to count cached classes from the classes endpoint
    try {
      const classesRes = await axios.get(`${API_BASE_URL}/api/classes`)
      if (classesRes.data && Array.isArray(classesRes.data)) {
        // Assume all classes have some cached data if the API is responding
        cacheStatus.value = {
          healthy: true,
          cachedClasses: classesRes.data.length || 16,
          lastUpdate: new Date().toISOString()
        }
      } else {
        cacheStatus.value = { healthy: false, cachedClasses: 0, lastUpdate: null }
      }
    } catch (fallbackError) {
      console.error('Fallback also failed:', fallbackError)
      cacheStatus.value = { healthy: false, cachedClasses: 0, lastUpdate: null }
    }
  }

  // Load health
  try {
    const healthRes = await axios.get(`${API_BASE_URL}/api/health`)
    const healthData = healthRes.data
    
    // Map the response to our expected format
    systemHealth.value = {
      apiStatus: healthData.status === 'healthy' ? 'Online' : healthData.status || 'Online',
      avgResponseTime: healthData.avgResponseTime || healthData.response_time_ms || 0,
      errorRate: healthData.errorRate || healthData.error_rate || 0
    }
  } catch (error) {
    console.error('Error loading health:', error)
    // If health check fails, API is likely down
    systemHealth.value = { apiStatus: 'Offline', avgResponseTime: 0, errorRate: 0 }
  }

  // Load activities
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const activitiesRes = await axios.get(`${API_BASE_URL}/api/admin/activities`, {
      headers: { Authorization: `Bearer ${token}` },
      params: {
        limit: 10  // Show last 10 activities
      }
    })
    // Handle both response formats
    if (activitiesRes.data.success && activitiesRes.data.data) {
      recentActivities.value = activitiesRes.data.data.activities || []
    } else if (activitiesRes.data.activities) {
      recentActivities.value = activitiesRes.data.activities
    } else if (Array.isArray(activitiesRes.data)) {
      recentActivities.value = activitiesRes.data
    } else {
      recentActivities.value = []
    }
    
    // Ensure activities have proper structure
    recentActivities.value = recentActivities.value.map(activity => ({
      ...activity,
      // Map backend fields to frontend expectations
      type: activity.action || activity.type,
      timestamp: activity.created_at || activity.timestamp || new Date().toISOString(),
      userAvatar: activity.user?.avatar_url || activity.userAvatar || null,
      userName: activity.user?.display_name || activity.userName || 'Unknown User',
      description: activity.description || formatActivityDescription(activity)
    }))
  } catch (error) {
    if (error.response?.status === 429) {
      console.warn('Rate limit reached for activities API')
    } else if (error.response?.status === 401) {
      console.warn('Authentication issue loading activities')
    } else if (error.response?.status !== undefined) {
      console.error('Error loading activities:', error.response.status, error.response.data)
    }
    // Show empty state if no activities can be loaded
    recentActivities.value = []
  }
  
  console.log('Recent activities loaded:', recentActivities.value)
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
  if (!timestamp) return 'Unknown'
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / (1000 * 60))
  if (minutes < 1) return 'Just now'
  if (minutes === 1) return '1m ago'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours === 1) return '1h ago'
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days === 1) return '1d ago'
  return `${days}d ago`
}

const getActivityIcon = (type) => {
  const icons = {
    // User actions
    login: 'fas fa-sign-in-alt',
    logout: 'fas fa-sign-out-alt',
    user_login: 'fas fa-sign-in-alt',
    user_register: 'fas fa-user-plus',
    user_create: 'fas fa-user-plus',
    user_update: 'fas fa-user-edit',
    token_refresh: 'fas fa-key',
    
    // Cache actions
    cache_refresh: 'fas fa-sync-alt',
    cache_clear: 'fas fa-trash-alt',
    
    // Scraping actions
    scrape_start: 'fas fa-download',
    scrape_complete: 'fas fa-check-circle',
    scrape_error: 'fas fa-exclamation-triangle',
    
    // Other actions
    spell_view: 'fas fa-eye',
    spell_search: 'fas fa-search',
    admin_action: 'fas fa-shield-alt',
    system_error: 'fas fa-exclamation-circle',
    api_error: 'fas fa-times-circle',
    error: 'fas fa-exclamation-triangle'
  }
  return icons[type] || 'fas fa-info-circle'
}

const isUserActivity = (type) => {
  return ['login', 'logout', 'user_login', 'user_register', 'user_create', 'user_update', 'admin_action'].includes(type)
}

const formatActivityDescription = (activity) => {
  // Format activity description from backend data
  const action = activity.action || activity.type
  const user = activity.user?.display_name || 'User'
  
  switch (action) {
    case 'login':
      return `${user} logged in`
    case 'logout':
      return `${user} logged out`
    case 'user_register':
    case 'user_create':
      return `${user} created account`
    case 'cache_refresh':
      return `Cache refreshed${activity.resource_type ? ' for ' + activity.resource_type : ''}`
    case 'cache_clear':
      return 'Cache cleared'
    case 'scrape_start':
      return `Started scraping ${activity.resource_type || 'data'}`
    case 'scrape_complete':
      return `Completed scraping ${activity.resource_type || 'data'}`
    case 'scrape_error':
      return `Error scraping ${activity.resource_type || 'data'}`
    default:
      return activity.description || `${action} performed`
  }
}

// Remove mock data generation - we'll use real data from the API

// Lifecycle
onMounted(async () => {
  await loadDashboardData()
  // Refresh dashboard data every 30 seconds
  refreshInterval = setInterval(loadDashboardData, 30000)
  
  // Refresh activities every 60 seconds to avoid rate limits
  activityRefreshInterval = setInterval(async () => {
    try {
      const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
      const activitiesRes = await axios.get(`${API_BASE_URL}/api/admin/activities`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { limit: 10 }
      })
      
      if (activitiesRes.data.activities) {
        recentActivities.value = activitiesRes.data.activities.map(activity => ({
          ...activity,
          type: activity.action || activity.type,
          timestamp: activity.created_at || activity.timestamp || new Date().toISOString(),
          userAvatar: activity.user?.avatar_url || null,
          userName: activity.user?.display_name || 'Unknown User',
          description: activity.description || formatActivityDescription(activity)
        }))
      }
    } catch (error) {
      // Silently fail for refresh intervals
      console.debug('Activity refresh failed:', error)
    }
  }, 60000) // Refresh activities every 60 seconds instead of 10
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  if (activityRefreshInterval) {
    clearInterval(activityRefreshInterval)
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
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.9) 0%, rgba(45, 55, 72, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 30px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.dashboard-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, transparent 0%, rgba(255, 255, 255, 0.02) 100%);
  pointer-events: none;
}

.dashboard-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4),
              0 0 0 1px rgba(255, 255, 255, 0.15) inset;
  border-color: rgba(255, 255, 255, 0.2);
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 1.8rem;
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.2) inset;
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
  font-size: 1.4rem;
  margin: 0;
  color: #f7fafc;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.01em;
}

.card-content {
  margin-bottom: 20px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-label {
  color: #9ca3af;
  font-size: 0.95rem;
  font-weight: 500;
  letter-spacing: 0.02em;
}

.stat-value {
  font-weight: 700;
  font-size: 1.2rem;
  color: #f7fafc;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.stat-value.success {
  color: #34d399;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

.stat-value.warning {
  color: #fbbf24;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

.card-actions {
  text-align: center;
}

.action-button {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-decoration: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.action-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.2) 50%, transparent 100%);
  transition: left 0.5s;
}

.action-button:hover::before {
  left: 100%;
}

.action-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

.quick-actions {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.9) 0%, rgba(45, 55, 72, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 35px;
  margin-bottom: 40px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.quick-actions::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.05) 0%, transparent 70%);
  pointer-events: none;
}

.quick-actions h2 {
  margin-bottom: 24px;
  color: #f7fafc;
  font-weight: 700;
  font-size: 1.8rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.quick-action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 32px 28px;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.05) inset;
}

/* Gradient background overlay */
.quick-action-btn::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.5s ease;
  pointer-events: none;
}

/* Icon background circle - removed as we're applying colors directly to buttons */

.quick-action-btn:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.4),
              0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(0, 0, 0, 0.4);
}

.quick-action-btn:hover::before {
  opacity: 1;
}

/* Removed hover::after as we're not using the circle anymore */

.quick-action-btn:active {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.2),
              inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

.quick-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  background: rgba(0, 0, 0, 0.2);
}

.quick-action-btn:disabled:hover {
  transform: none;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1),
              inset 0 1px 0 rgba(255, 255, 255, 0.5);
  border-color: rgba(255, 255, 255, 0.3);
}

/* Button-specific gradient backgrounds */
.action-grid button:nth-child(1) {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.05) 100%);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.action-grid button:nth-child(1):hover {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.25) 0%, rgba(16, 185, 129, 0.15) 100%);
  border-color: rgba(16, 185, 129, 0.4);
  box-shadow: 0 12px 35px rgba(16, 185, 129, 0.3),
              inset 0 0 0 1px rgba(16, 185, 129, 0.2);
}

.action-grid button:nth-child(2) {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(59, 130, 246, 0.05) 100%);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.action-grid button:nth-child(2):hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.25) 0%, rgba(59, 130, 246, 0.15) 100%);
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 12px 35px rgba(59, 130, 246, 0.3),
              inset 0 0 0 1px rgba(59, 130, 246, 0.2);
}

.action-grid button:nth-child(3) {
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.15) 0%, rgba(251, 146, 60, 0.05) 100%);
  border: 1px solid rgba(251, 146, 60, 0.2);
}

.action-grid button:nth-child(3):hover {
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.25) 0%, rgba(251, 146, 60, 0.15) 100%);
  border-color: rgba(251, 146, 60, 0.4);
  box-shadow: 0 12px 35px rgba(251, 146, 60, 0.3),
              inset 0 0 0 1px rgba(251, 146, 60, 0.2);
}

.action-grid button:nth-child(4) {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(168, 85, 247, 0.05) 100%);
  border: 1px solid rgba(168, 85, 247, 0.2);
}

.action-grid button:nth-child(4):hover {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.25) 0%, rgba(168, 85, 247, 0.15) 100%);
  border-color: rgba(168, 85, 247, 0.4);
  box-shadow: 0 12px 35px rgba(168, 85, 247, 0.3),
              inset 0 0 0 1px rgba(168, 85, 247, 0.2);
}

.quick-action-btn i {
  font-size: 2.8rem;
  z-index: 1;
  transition: all 0.3s ease;
  position: relative;
  margin-bottom: 4px;
}

/* Icon colors matching button theme */
.action-grid button:nth-child(1) i {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 2px 4px rgba(16, 185, 129, 0.2));
}

.action-grid button:nth-child(2) i {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 2px 4px rgba(59, 130, 246, 0.2));
}

.action-grid button:nth-child(3) i {
  background: linear-gradient(135deg, #fb923c 0%, #f97316 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 2px 4px rgba(251, 146, 60, 0.2));
}

.action-grid button:nth-child(4) i {
  background: linear-gradient(135deg, #a855f7 0%, #9333ea 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 2px 4px rgba(168, 85, 247, 0.2));
}

.quick-action-btn:hover i {
  transform: translateY(-2px) scale(1.15);
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.15));
}

.quick-action-btn span {
  font-weight: 600;
  font-size: 1.05rem;
  color: #f7fafc;
  z-index: 1;
  transition: all 0.3s ease;
  letter-spacing: 0.02em;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.quick-action-btn:hover span {
  color: #ffffff;
  transform: translateY(1px);
}

.recent-activity {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.9) 0%, rgba(45, 55, 72, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 35px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.recent-activity h2 {
  margin-bottom: 24px;
  color: #f7fafc;
  font-weight: 700;
  font-size: 1.8rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.activity-list {
  max-height: 400px;
  overflow-y: auto;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 15px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  width: 45px;
  height: 45px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.activity-avatar {
  width: 45px;
  height: 45px;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.2);
}

.activity-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* User action icons */
.activity-icon.login,
.activity-icon.user_login {
  background: rgba(14, 165, 233, 0.2);
  color: #38bdf8;
  border: 1px solid rgba(14, 165, 233, 0.3);
}

.activity-icon.logout {
  background: rgba(156, 163, 175, 0.2);
  color: #9ca3af;
  border: 1px solid rgba(156, 163, 175, 0.3);
}

.activity-icon.user_register,
.activity-icon.user_create {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.activity-icon.user_update {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

/* Cache action icons */
.activity-icon.cache_refresh {
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.activity-icon.cache_clear {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

/* Scraping action icons */
.activity-icon.scrape_start {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.activity-icon.scrape_complete {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.activity-icon.scrape_error {
  background: rgba(251, 146, 60, 0.2);
  color: #fb923c;
  border: 1px solid rgba(251, 146, 60, 0.3);
}

/* Other action icons */
.activity-icon.spell_view,
.activity-icon.spell_search {
  background: rgba(99, 102, 241, 0.2);
  color: #818cf8;
  border: 1px solid rgba(99, 102, 241, 0.3);
}

.activity-icon.admin_action {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.activity-icon.error,
.activity-icon.system_error,
.activity-icon.api_error {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

/* Add default user icon size for activities without avatars */
.activity-icon.login i,
.activity-icon.user_login i,
.activity-icon.user_register i,
.activity-icon.user_create i {
  font-size: 1.3rem;
}

.activity-content {
  flex: 1;
}

.activity-description {
  margin: 0 0 5px 0;
  font-weight: 600;
  color: #f7fafc;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.activity-time {
  color: #9ca3af;
  font-size: 0.85rem;
}

.no-activity {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
}

/* Add animation for the spinning icons */
@keyframes gentlePulse {
  0%, 100% {
    opacity: 0.8;
  }
  50% {
    opacity: 1;
  }
}

.quick-action-btn .fa-spin {
  animation: fa-spin 1s infinite linear, gentlePulse 2s infinite ease-in-out;
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
  
  .quick-action-btn {
    padding: 15px;
  }
  
  .quick-action-btn i {
    font-size: 1.5rem;
  }
  
  .quick-action-btn span {
    font-size: 0.85rem;
  }
}
</style>