<template>
  <div class="admin-logs">
    <div class="page-header">
      <div class="header-content">
        <router-link to="/admin" class="back-link">
          <i class="fas fa-arrow-left"></i>
          Back to Dashboard
        </router-link>
        <h1>System Logs</h1>
        <p class="subtitle">View and filter system logs and activity</p>
      </div>
    </div>

    <!-- Log Filters -->
    <div class="filters-section">
      <div class="filters-row">
        <div class="filter-group">
          <label>Log Level</label>
          <select v-model="filters.level" class="filter-select">
            <option value="">All Levels</option>
            <option value="error">Error</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
            <option value="debug">Debug</option>
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
            placeholder="Search logs..."
            class="filter-input"
          >
        </div>
        
        <button @click="refreshLogs" class="refresh-btn">
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
          <div class="log-message">{{ log.message }}</div>
          <div v-if="log.details" class="log-details">
            <pre>{{ log.details }}</pre>
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
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()

// API base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (import.meta.env.PROD ? 'https://eqdatascraper-backend-production.up.railway.app' : 'http://localhost:5001')

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

// Mock data generator (remove when backend endpoint is ready)
const generateMockLogs = () => {
  const levels = ['info', 'warning', 'error', 'debug']
  const sources = ['backend/app.py', 'auth.py', 'scraper.py', 'cache.py']
  const messages = [
    'Cache loaded from disk',
    'User authentication successful',
    'Spell data scraping completed',
    'Rate limit exceeded for IP',
    'Database connection established',
    'Cache refresh triggered',
    'API endpoint accessed',
    'Background task started'
  ]
  
  return Array.from({ length: 100 }, (_, i) => ({
    id: i + 1,
    timestamp: new Date(Date.now() - Math.random() * 86400000).toISOString(),
    level: levels[Math.floor(Math.random() * levels.length)],
    source: sources[Math.floor(Math.random() * sources.length)],
    message: messages[Math.floor(Math.random() * messages.length)],
    details: Math.random() > 0.7 ? 'Additional details about this log entry...' : null
  })).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
}

// Lifecycle
onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.admin-logs {
  padding: 20px;
  padding-top: 80px; /* Add padding to account for fixed header elements */
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
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
  color: #666;
  font-size: 1.1rem;
  margin: 0;
}

.filters-section {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
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
  color: #4a5568;
  font-size: 0.9rem;
}

.filter-select,
.filter-input {
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 1rem;
  background: white;
}

.filter-select:focus,
.filter-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
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
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
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
  color: #666;
  gap: 10px;
}

.no-logs i {
  font-size: 3rem;
  color: #cbd5e0;
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
  background: #f7fafc;
}

.log-entry.error {
  border-left-color: #ef4444;
  background: #fef2f2;
}

.log-entry.warning {
  border-left-color: #f59e0b;
  background: #fffbeb;
}

.log-entry.info {
  border-left-color: #3b82f6;
  background: #eff6ff;
}

.log-entry.debug {
  border-left-color: #6b7280;
  background: #f9fafb;
}

.log-header {
  display: flex;
  gap: 15px;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.log-time {
  color: #6b7280;
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
  color: #6b7280;
  font-size: 0.85rem;
  font-family: monospace;
}

.log-message {
  color: #1a202c;
  line-height: 1.5;
}

.log-details {
  margin-top: 10px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.log-details pre {
  margin: 0;
  font-size: 0.85rem;
  color: #4a5568;
  white-space: pre-wrap;
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
  border: 1px solid #e5e7eb;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #666;
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