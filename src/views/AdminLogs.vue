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
            <option value="login">Login</option>
            <option value="logout">Logout</option>
            <option value="spell_search">Spell Search</option>
            <option value="spell_view">Spell View</option>
            <option value="cache_refresh">Cache Refresh</option>
            <option value="cache_clear">Cache Clear</option>
            <option value="scrape_start">Scrape Start</option>
            <option value="scrape_complete">Scrape Complete</option>
            <option value="admin_action">Admin Action</option>
            <option value="system_error">System Error</option>
          </select>
        </div>
        
        <div class="filter-group">
          <label>Resource Type</label>
          <select v-model="filters.resource_type" class="filter-select">
            <option value="">All Resources</option>
            <option value="user">User</option>
            <option value="session">Session</option>
            <option value="spell">Spell</option>
            <option value="class">Class</option>
            <option value="cache">Cache</option>
            <option value="system">System</option>
          </select>
        </div>
        
        <div class="filter-group">
          <label>Time Range</label>
          <select v-model="filters.timeRange" class="filter-select">
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
        
        <button @click="refreshActivities" class="refresh-btn">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
          Refresh
        </button>
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
        >
          <div class="log-header">
            <span class="log-time">{{ formatDateTime(log.timestamp) }}</span>
            <span class="log-level" :class="log.level">{{ log.level.toUpperCase() }}</span>
            <span class="log-source">{{ log.source }}</span>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import { API_BASE_URL, buildApiUrl, API_ENDPOINTS } from '../config/api'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()

// State
const logs = ref([])
const loading = ref(false)
const filters = ref({
  level: '',
  timeRange: '24h',
  search: ''
})
const currentPage = ref(1)
const perPage = ref(50)
const expandedLogs = ref({})

// Computed
const filteredLogs = computed(() => {
  return logs.value.filter(log => {
    if (filters.value.level && log.level !== filters.value.level) return false
    if (filters.value.search) {
      const searchLower = filters.value.search.toLowerCase()
      return log.message.toLowerCase().includes(searchLower) ||
             log.source?.toLowerCase().includes(searchLower)
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
const loadLogs = async () => {
  loading.value = true
  try {
    // For now, use mock data since the endpoint might not exist
    logs.value = generateMockLogs()
    
    // When backend endpoint is ready, use this:
    // const response = await axios.get(`${API_BASE_URL}/api/admin/logs`, {
    //   headers: { Authorization: `Bearer ${userStore.accessToken}` },
    //   params: { timeRange: filters.value.timeRange }
    // })
    // logs.value = response.data.data
  } catch (error) {
    console.error('Error loading logs:', error)
  } finally {
    loading.value = false
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

// Mock data generator (remove when backend endpoint is ready)
const generateMockLogs = () => {
  const logTemplates = [
    {
      level: 'info',
      source: 'backend/app.py',
      message: 'Cache loaded from disk',
      details: {
        spellClasses: 16,
        totalSpells: 1532,
        pricingEntries: 1038,
        loadTime: '2.3s',
        cacheSize: '4.2MB'
      }
    },
    {
      level: 'info',
      source: 'auth.py',
      message: 'User rgagnier06@gmail.com authenticated successfully via Google OAuth from IP 192.168.1.45',
      details: {
        user: 'rgagnier06@gmail.com',
        provider: 'Google OAuth',
        ipAddress: '192.168.1.45',
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        sessionId: 'sess_2a3b4c5d6e7f8g9h',
        isNewUser: false,
        loginMethod: 'OAuth'
      }
    },
    {
      level: 'warning',
      source: 'scraper.py',
      message: 'Necromancer spell scraping completed with 4 failures (380/384 successful) in 45.2s - 98.96% success rate',
      details: {
        class: 'Necromancer',
        totalSpells: 384,
        successfulScrapes: 380,
        failedScrapes: 4,
        failedSpellIds: [2756, 3891, 4102, 5234],
        duration: '45.2s',
        retryAttempts: 3,
        successRate: '98.96%'
      }
    },
    {
      level: 'warning',
      source: 'backend/app.py',
      message: 'Rate limit exceeded for IP 45.23.178.92 on /api/spell-details/:id - 156 requests in 1 minute (limit: 100) - blocked for 5 minutes',
      details: {
        ipAddress: '45.23.178.92',
        endpoint: '/api/spell-details/:id',
        requestCount: 156,
        timeWindow: '1 minute',
        limit: 100,
        blockDuration: '5 minutes',
        userAgent: 'Python/3.8 requests/2.25.1',
        user: null
      }
    },
    {
      level: 'debug',
      source: 'backend/app.py',
      message: 'Database connection established',
      details: {
        host: 'shuttle.proxy.rlwy.net',
        port: 56963,
        database: 'railway',
        sslEnabled: true,
        poolSize: 20,
        connectionTime: '132ms'
      }
    },
    {
      level: 'info',
      source: 'cache.py',
      message: 'Cache refresh triggered by automatic expiry check for Cleric and Wizard - cache was 26.5 hours old (expires at 24 hours)',
      details: {
        triggeredBy: 'Automatic expiry check',
        classes: ['Cleric', 'Wizard'],
        previousCacheAge: '26.5 hours',
        expiryThreshold: '24 hours'
      }
    },
    {
      level: 'debug',
      source: 'backend/app.py',
      message: 'API endpoint accessed',
      details: null // Some logs don't have details
    },
    {
      level: 'info',
      source: 'scraper.py',
      message: 'Background task started',
      details: {
        taskType: 'Full spell refresh',
        scheduledBy: 'System',
        estimatedDuration: '10-15 minutes',
        priority: 'low'
      }
    },
    {
      level: 'error',
      source: 'scraper.py',
      message: 'Failed to scrape Druid spell "Harvest" (ID: 3456) from alla.clumsysworld.com - HTTP 503 after 3 retries over 15.3s',
      details: {
        spellId: 3456,
        spellName: 'Harvest',
        spellClass: 'Druid',
        error: 'HTTP 503 Service Unavailable',
        url: 'https://alla.clumsysworld.com/spell.php?id=3456',
        retryCount: 3,
        lastAttempt: new Date().toISOString(),
        totalDuration: '15.3s'
      }
    },
    {
      level: 'warning',
      source: 'backend/app.py',
      message: 'Slow API response: GET /api/spells/wizard took 850ms (threshold: 500ms) - returned 384 items for user rgagnier06@gmail.com from IP 192.168.1.45',
      details: {
        endpoint: 'GET /api/spells/wizard',
        responseTime: '850ms',
        threshold: '500ms',
        itemsReturned: 384,
        cacheHit: false,
        user: 'rgagnier06@gmail.com',
        ipAddress: '192.168.1.45'
      }
    },
    {
      level: 'info',
      source: 'backend/app.py',
      message: 'Database backup completed',
      details: {
        tablesBackedUp: ['spell_cache', 'pricing_cache', 'spell_details_cache', 'users', 'sessions'],
        totalRecords: 15243,
        backupSize: '45.2MB',
        duration: '3.2s',
        location: 's3://eq-backups/2025-07-05/backup-1720123456.sql.gz'
      }
    },
    {
      level: 'error',
      source: 'auth.py',
      message: 'OAuth authentication failed for user@example.com from IP 192.168.1.100 - Google provider error: Invalid client_id',
      details: {
        provider: 'Google',
        error: 'Invalid client_id',
        ipAddress: '192.168.1.100',
        attemptedEmail: 'user@example.com'
      }
    }
  ]
  
  return Array.from({ length: 50 }, (_, i) => {
    const template = logTemplates[Math.floor(Math.random() * logTemplates.length)]
    const hasDetails = template.details !== null && Math.random() > 0.3 // 70% chance of having details
    
    return {
      id: i + 1,
      timestamp: new Date(Date.now() - Math.random() * 86400000).toISOString(),
      level: template.level,
      source: template.source,
      message: template.message,
      details: hasDetails ? template.details : null
    }
  }).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
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

.log-source {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
  font-family: monospace;
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