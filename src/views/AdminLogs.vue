<template>
  <div class="admin-logs">
    <div class="page-header">
      <div class="header-content">
        <router-link to="/admin" class="back-link">
          <i class="fas fa-arrow-left"></i>
          Back to Dashboard
        </router-link>
        <h1>Activity Logs</h1>
        <p class="subtitle">View and filter user activities and system events</p>
      </div>
    </div>

    <!-- Activity Filters -->
    <div class="filters-section">
      <div class="filters-row">
        <div class="filter-group">
          <label>Action Type</label>
          <select v-model="filters.action" class="filter-select">
            <option value="">All Actions</option>
            <option value="item_search">Item Search</option>
            <option value="spell_search">Spell Search</option>
            <option value="login">Login</option>
            <option value="logout">Logout</option>
            <option value="admin_action">Admin Action</option>
            <option value="logs_cleared">Logs Cleared</option>
            <option value="system_monitoring">System Monitoring</option>
            <option value="database_query">Database Query</option>
            <option value="error">System Error</option>
          </select>
        </div>
        
        <div class="filter-group">
          <label>Resource Type</label>
          <select v-model="filters.resource_type" class="filter-select">
            <option value="">All Resources</option>
            <option value="item">Item</option>
            <option value="spell">Spell</option>
            <option value="user">User</option>
            <option value="session">Session</option>
            <option value="database">Database</option>
            <option value="system">System</option>
            <option value="logs">Logs</option>
          </select>
        </div>
        
        <div class="filter-group">
          <label>Time Range</label>
          <select v-model="filters.timeRange" class="filter-select">
            <option value="">All Time</option>
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>
        
        <div class="filter-group">
          <label>Search</label>
          <input 
            v-model="filters.search" 
            type="text" 
            placeholder="Search activities..."
            class="filter-input"
          >
        </div>
        
        <button @click="refreshLogs" class="refresh-btn">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
          Refresh
        </button>
        
        <button 
          @click="showClearConfirmation = true" 
          class="clear-logs-btn"
          :disabled="!oauthEnabled"
          :title="!oauthEnabled ? 'Log clearing requires OAuth to be enabled' : ''"
        >
          <i class="fas fa-trash-alt"></i>
          Clear Logs
        </button>
      </div>
    </div>

    <!-- OAuth Status Warning -->
    <div v-if="!oauthEnabled" class="oauth-warning">
      <div class="warning-content">
        <i class="fas fa-exclamation-triangle"></i>
        <div class="warning-text">
          <h4>Limited Functionality</h4>
          <p>OAuth is disabled. Log clearing and advanced monitoring features are not available.</p>
        </div>
      </div>
    </div>

    <!-- Logs Display -->
    <div class="logs-container">
      <div v-if="loading" class="loading">
        <i class="fas fa-spinner fa-spin"></i>
        Loading logs...
      </div>
      
      <div v-else-if="filteredLogs.length === 0" class="no-logs">
        <i class="fas fa-file-alt"></i>
        <p>No logs found</p>
      </div>
      
      <div v-else class="logs-list">
        <div 
          v-for="log in paginatedLogs" 
          :key="log.id"
          class="log-entry"
          :class="log.level"
          :data-source="log.source"
        >
          <div class="log-header">
            <span class="log-time">{{ formatDateTime(log.timestamp) }}</span>
            <span class="log-level" :class="log.level">{{ log.level.toUpperCase() }}</span>
            <span v-if="log.context" class="log-context">{{ log.context }}</span>
            <span v-if="log.source" class="log-source">{{ log.source }}</span>
            <span v-if="log.responseTime" class="response-time">{{ log.responseTime }}</span>
          </div>
          <div class="log-content">
            <div class="log-message">{{ log.message }}</div>
            <button 
              v-if="log.details && !expandedLogs[log.id]" 
              @click="toggleLogDetails(log.id)"
              class="expand-btn"
            >
              <i class="fas fa-chevron-right"></i>
              Show Details
            </button>
          </div>
          <div v-if="log.details && expandedLogs[log.id]" class="log-details expanded">
            <button @click="toggleLogDetails(log.id)" class="collapse-btn">
              <i class="fas fa-chevron-down"></i>
              Hide Details
            </button>
            <div class="details-content">
              <div v-for="(value, key) in log.details" :key="key" class="detail-item">
                <span class="detail-key">{{ formatDetailKey(key) }}:</span>
                <span class="detail-value">{{ formatDetailValue(value) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <button 
        @click="currentPage--" 
        :disabled="currentPage === 1"
        class="page-btn"
      >
        <i class="fas fa-chevron-left"></i>
      </button>
      <span class="page-info">
        Page {{ currentPage }} of {{ totalPages }}
      </span>
      <button 
        @click="currentPage++" 
        :disabled="currentPage === totalPages"
        class="page-btn"
      >
        <i class="fas fa-chevron-right"></i>
      </button>
    </div>

    <!-- Clear Logs Confirmation Modal -->
    <div v-if="showClearConfirmation" class="modal-overlay" @click="showClearConfirmation = false">
      <div class="confirmation-modal" @click.stop>
        <div class="modal-header">
          <h3>Clear System Logs</h3>
          <button @click="showClearConfirmation = false" class="close-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-content">
          <p>Are you sure you want to clear all system logs? This action cannot be undone.</p>
          <p class="warning-text">This will clear:</p>
          <ul class="clear-items-list">
            <li>Application logs</li>
            <li>Error logs</li>
            <li>Monitor logs</li>
            <li>Performance logs</li>
          </ul>
        </div>
        <div class="modal-actions">
          <button @click="showClearConfirmation = false" class="cancel-btn">
            Cancel
          </button>
          <button @click="clearLogs" class="confirm-btn" :disabled="clearingLogs">
            <i v-if="clearingLogs" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-trash-alt"></i>
            {{ clearingLogs ? 'Clearing...' : 'Clear Logs' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <ToastNotification
      ref="toast"
      :title="toastConfig.title"
      :message="toastConfig.message"
      :details="toastConfig.details"
      :type="toastConfig.type"
      :duration="toastConfig.duration"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import { API_BASE_URL, buildApiUrl, API_ENDPOINTS } from '../config/api'
import axios from 'axios'
import ToastNotification from '../components/ToastNotification.vue'

const router = useRouter()
const userStore = useUserStore()

// State
const logs = ref([])
const loading = ref(false)
const showClearConfirmation = ref(false)
const clearingLogs = ref(false)
const oauthEnabled = ref(true) // Assume enabled initially, will be detected
const toast = ref(null)
const toastConfig = ref({
  title: '',
  message: '',
  details: [],
  type: 'info',
  duration: 5000
})
const filters = ref({
  level: '',
  action: '',
  resource_type: '',
  timeRange: '',
  search: ''
})
const currentPage = ref(1)
const perPage = ref(50)
const expandedLogs = ref({})

// Computed
const filteredLogs = computed(() => {
  return logs.value.filter(log => {
    // Level filter
    if (filters.value.level && log.level !== filters.value.level) return false
    
    // Action type filter - check both source and message content
    if (filters.value.action) {
      const action = filters.value.action
      const message = log.message?.toLowerCase() || ''
      const source = log.source?.toLowerCase() || ''
      
      let matches = false
      switch (action) {
        case 'item_search':
          matches = source === 'item_search' || message.includes('item search')
          break
        case 'spell_search':
          matches = source === 'spell_search' || message.includes('spell search')
          break
        case 'system_monitoring':
          matches = message.includes('system resources') || message.includes('cpu') || message.includes('memory')
          break
        case 'database_query':
          matches = message.includes('query') || message.includes('database')
          break
        case 'logs_cleared':
          matches = message.includes('cleared') || message.includes('reset')
          break
        case 'login':
          matches = message.includes('login') || message.includes('logged in')
          break
        case 'logout':
          matches = message.includes('logout') || message.includes('logged out')
          break
        case 'admin_action':
          matches = message.includes('admin') || source.includes('admin')
          break
        case 'error':
          matches = log.level === 'error' || message.includes('error') || message.includes('failed')
          break
        default:
          matches = source === action
      }
      if (!matches) return false
    }
    
    // Resource type filter - check message content for resource references
    if (filters.value.resource_type) {
      const resourceType = filters.value.resource_type
      const message = log.message?.toLowerCase() || ''
      
      let matches = false
      switch (resourceType) {
        case 'item':
          matches = message.includes('item')
          break
        case 'spell':
          matches = message.includes('spell')
          break
        case 'user':
          matches = message.includes('user') || message.includes('login') || message.includes('logout')
          break
        case 'session':
          matches = message.includes('session')
          break
        case 'database':
          matches = message.includes('database') || message.includes('query') || message.includes('timeline')
          break
        case 'system':
          matches = message.includes('system') || message.includes('cpu') || message.includes('memory')
          break
        case 'logs':
          matches = message.includes('log') || message.includes('cleared')
          break
        default:
          matches = true
      }
      if (!matches) return false
    }
    
    // Time range filter
    if (filters.value.timeRange) {
      const now = new Date()
      const logTime = new Date(log.timestamp)
      const timeDiff = now - logTime
      
      let maxAge = 0
      switch (filters.value.timeRange) {
        case '1h':
          maxAge = 60 * 60 * 1000 // 1 hour in milliseconds
          break
        case '24h':
          maxAge = 24 * 60 * 60 * 1000 // 24 hours in milliseconds
          break
        case '7d':
          maxAge = 7 * 24 * 60 * 60 * 1000 // 7 days in milliseconds
          break
        case '30d':
          maxAge = 30 * 24 * 60 * 60 * 1000 // 30 days in milliseconds
          break
      }
      
      if (timeDiff > maxAge) return false
    }
    
    // Search text filter
    if (filters.value.search) {
      const searchLower = filters.value.search.toLowerCase()
      const matchesMessage = log.message?.toLowerCase().includes(searchLower)
      const matchesSource = log.source?.toLowerCase().includes(searchLower)
      const matchesContext = log.context?.toLowerCase().includes(searchLower)
      
      if (!matchesMessage && !matchesSource && !matchesContext) return false
    }
    
    return true
  })
})

const paginatedLogs = computed(() => {
  const start = (currentPage.value - 1) * perPage.value
  const end = start + perPage.value
  return filteredLogs.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredLogs.value.length / perPage.value)
})

// Methods
const showToast = (title, message, details = [], type = 'info', duration = 5000) => {
  toastConfig.value = { title, message, details, type, duration }
  if (toast.value) {
    toast.value.show()
  }
}

const formatCategoryMessage = (categories) => {
  const parts = []
  if (categories.error_logs > 0) parts.push(`${categories.error_logs} error logs`)
  if (categories.performance_metrics > 0) parts.push(`${categories.performance_metrics} performance metrics`)
  if (categories.system_metrics > 0) parts.push(`${categories.system_metrics} system metrics`)
  if (categories.log_files > 0) parts.push(`${categories.log_files} log files`)
  if (categories.monitoring_data > 0) parts.push(`${categories.monitoring_data} monitoring data sources`)
  return parts
}

const loadLogs = async () => {
  loading.value = true
  try {
    // Try to load logs from the admin endpoint
    const headers = userStore.accessToken ? 
      { Authorization: `Bearer ${userStore.accessToken}` } : {}
    
    const response = await axios.get(`${API_BASE_URL}/api/logs`, {
      headers,
      params: { 
        level: filters.value.level || 'all',
        limit: 100
      }
    })
    
    if (response.data.success) {
      logs.value = response.data.data.logs || []
      // Detect if OAuth is enabled based on response
      oauthEnabled.value = !response.data.data.message?.includes('OAuth is disabled')
    } else {
      console.error('Failed to load logs:', response.data.error)
      logs.value = []
    }
  } catch (error) {
    console.error('Error loading logs:', error)
    
    // Check if it's a 403 or auth error, indicating OAuth is disabled
    if (error.response?.status === 403 || error.response?.status === 401) {
      oauthEnabled.value = false
      // Try to get minimal logs from admin_minimal endpoint
      try {
        const minimalResponse = await axios.get(`${API_BASE_URL}/api/admin/system/logs`)
        if (minimalResponse.data.success) {
          logs.value = minimalResponse.data.data.logs || []
        }
      } catch (minimalError) {
        console.error('Failed to load minimal logs:', minimalError)
        logs.value = []
      }
    } else {
      // Other error, show empty logs
      logs.value = []
    }
  } finally {
    loading.value = false
  }
}

const clearLogs = async () => {
  if (!oauthEnabled.value) {
    showToast('OAuth Required', 'Log clearing requires OAuth to be enabled', [], 'warning')
    return
  }
  
  clearingLogs.value = true
  try {
    const headers = userStore.accessToken ? 
      { Authorization: `Bearer ${userStore.accessToken}` } : {}
    
    const response = await axios.post(`${API_BASE_URL}/api/logs/clear`, {}, {
      headers
    })
    
    if (response.data.success) {
      showClearConfirmation.value = false
      
      // Format success message with categorized breakdown
      const { categories, cleared_items } = response.data.data
      const categoryDetails = formatCategoryMessage(categories)
      
      showToast(
        'Logs Cleared Successfully', 
        `Cleared ${cleared_items.length} log sources`, 
        categoryDetails,
        'success',
        7000
      )
      
      // Reload logs to show the new log event
      await loadLogs()
    } else {
      console.error('Failed to clear logs:', response.data.error)
      showToast('Clear Failed', response.data.error, [], 'error')
    }
  } catch (error) {
    console.error('Error clearing logs:', error)
    if (error.response?.status === 403) {
      showToast('Authentication Error', 'Log clearing requires OAuth to be enabled', [], 'error')
    } else {
      const errorMsg = error.response?.data?.error || error.message
      showToast('Clear Failed', errorMsg, [], 'error')
    }
  } finally {
    clearingLogs.value = false
  }
}

const refreshLogs = () => {
  currentPage.value = 1
  loadLogs()
}

const formatDateTime = (timestamp) => {
  return new Date(timestamp).toLocaleString()
}

const toggleLogDetails = (logId) => {
  expandedLogs.value[logId] = !expandedLogs.value[logId]
}

const formatDetailKey = (key) => {
  // Convert camelCase to Title Case
  return key
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim()
}

const formatDetailValue = (value) => {
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value, null, 2)
  }
  return value
}


// Lifecycle
onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.admin-logs {
  padding: 20px;
  padding-top: 100px; /* Increased padding to prevent logo overlap */
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
  margin-top: 20px; /* Add space from top */
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.back-link:hover {
  color: #764ba2;
}

.page-header h1 {
  font-size: 2.5rem;
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.1rem;
  margin: 0;
}

.filters-section {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.85) 0%, rgba(45, 55, 72, 0.85) 100%);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 20px;
  margin-bottom: 20px;
}

.filters-row {
  display: flex;
  gap: 20px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-width: 200px;
}

.filter-group label {
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
}

.filter-select,
.filter-input {
  padding: 10px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  font-size: 1rem;
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.filter-select:focus,
.filter-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3);
  background: rgba(255, 255, 255, 0.15);
}

.filter-select option {
  background: #2d3748;
  color: white;
}

.filter-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.refresh-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.refresh-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.clear-logs-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.clear-logs-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
}

.clear-logs-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: rgba(239, 68, 68, 0.3);
}

.oauth-warning {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 12px;
  margin-bottom: 20px;
  overflow: hidden;
}

.warning-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
}

.oauth-warning i {
  color: #f59e0b;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.warning-text h4 {
  color: #f59e0b;
  margin: 0 0 4px 0;
  font-size: 1rem;
  font-weight: 600;
}

.warning-text p {
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.4;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.confirmation-modal {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(45, 55, 72, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 0;
  margin-bottom: 16px;
}

.modal-header h3 {
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 4px;
  border-radius: 4px;
  transition: color 0.2s;
}

.close-btn:hover {
  color: rgba(255, 255, 255, 0.9);
}

.modal-content {
  padding: 0 24px 20px;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
}

.warning-text {
  color: #f59e0b;
  font-weight: 500;
  margin-top: 16px;
  margin-bottom: 8px;
}

.clear-items-list {
  margin: 0;
  padding-left: 20px;
  color: rgba(255, 255, 255, 0.7);
}

.clear-items-list li {
  margin-bottom: 4px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 20px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.cancel-btn {
  padding: 10px 20px;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.cancel-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.9);
}

.confirm-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.confirm-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.confirm-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.logs-container {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.85) 0%, rgba(45, 55, 72, 0.85) 100%);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 20px;
  min-height: 400px;
}

.loading,
.no-logs {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: rgba(255, 255, 255, 0.7);
  gap: 10px;
}

.no-logs i {
  font-size: 3rem;
  color: rgba(255, 255, 255, 0.3);
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.log-entry {
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid;
  background: rgba(255, 255, 255, 0.05);
  transition: background 0.2s;
}

.log-entry:hover {
  background: rgba(255, 255, 255, 0.08);
}

.log-entry.error {
  border-left-color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.log-entry.error:hover {
  background: rgba(239, 68, 68, 0.15);
}

.log-entry.warning {
  border-left-color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
}

.log-entry.warning:hover {
  background: rgba(245, 158, 11, 0.15);
}

.log-entry.info {
  border-left-color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
}

.log-entry.info:hover {
  background: rgba(59, 130, 246, 0.15);
}

.log-entry.debug {
  border-left-color: #6b7280;
  background: rgba(107, 114, 128, 0.1);
}

.log-entry.debug:hover {
  background: rgba(107, 114, 128, 0.15);
}

/* Search event specific styling */
.log-entry[data-source*="search"] {
  border-left-color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.log-entry[data-source*="search"]:hover {
  background: rgba(16, 185, 129, 0.15);
}

.log-entry[data-source="item_search"] .log-source::before {
  content: "🔍 ";
}

.log-entry[data-source="spell_search"] .log-source::before {
  content: "✨ ";
}

.log-header {
  display: flex;
  gap: 15px;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.log-time {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.85rem;
}

.log-level {
  font-weight: 600;
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 4px;
}

.log-level.error {
  background: #ef4444;
  color: white;
}

.log-level.warning {
  background: #f59e0b;
  color: white;
}

.log-level.info {
  background: #3b82f6;
  color: white;
}

.log-level.debug {
  background: #6b7280;
  color: white;
}

.log-context {
  color: #667eea;
  font-size: 0.85rem;
  font-weight: 500;
  background: rgba(102, 126, 234, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid rgba(102, 126, 234, 0.3);
}

.log-source {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
  font-family: monospace;
}

.response-time {
  color: #f59e0b;
  font-size: 0.8rem;
  font-weight: 500;
  background: rgba(245, 158, 11, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.log-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.log-message {
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.5;
  flex: 1;
}

.expand-btn,
.collapse-btn {
  padding: 6px 14px;
  font-size: 0.8rem;
  font-weight: 500;
  border: 1px solid rgba(102, 126, 234, 0.3);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  color: #667eea;
  border-radius: 6px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.expand-btn:hover,
.collapse-btn:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
}

.expand-btn i,
.collapse-btn i {
  font-size: 0.7rem;
  transition: transform 0.2s;
}

.expand-btn:hover i {
  transform: translateX(2px);
}

.collapse-btn i {
  transform: rotate(90deg);
}

.log-details {
  margin-top: 12px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  animation: slideDown 0.2s ease-out;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.log-details .collapse-btn {
  margin-bottom: 12px;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.details-content {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.detail-key {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  min-width: 140px;
  font-size: 0.85rem;
}

.detail-value {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
  font-family: monospace;
  word-break: break-word;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 30px;
}

.page-btn {
  padding: 8px 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.9);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.2);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

@media (max-width: 768px) {
  .filters-row {
    flex-direction: column;
  }
  
  .filter-group {
    width: 100%;
  }
}
</style>