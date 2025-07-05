<template>
  <div class="admin-cache">
    <div class="page-header">
      <div class="header-content">
        <router-link to="/admin" class="back-link">
          <i class="fas fa-arrow-left"></i>
          Back to Dashboard
        </router-link>
        <h1>Cache Management</h1>
        <p class="subtitle">Monitor and manage spell data caching</p>
      </div>
    </div>

    <!-- Cache Overview -->
    <div class="cache-overview">
      <div class="overview-card">
        <div class="card-icon">
          <i class="fas fa-server"></i>
        </div>
        <div class="card-content">
          <h3>Cache Status</h3>
          <div class="status-indicator" :class="cacheHealthClass">
            <i :class="cacheHealthIcon"></i>
            {{ cacheHealthText }}
          </div>
          <div class="cache-stats">
            <div class="stat">
              <span class="label">Total Cached:</span>
              <span class="value">{{ cacheStatus.total_cached || 0 }} / 16 classes</span>
            </div>
            <div class="stat">
              <span class="label">Cache Size:</span>
              <span class="value">{{ formatBytes(cacheStatus.total_size || 0) }}</span>
            </div>
            <div class="stat">
              <span class="label">Last Update:</span>
              <span class="value">{{ formatLastUpdate(cacheStatus.last_update) }}</span>
            </div>
          </div>
        </div>
        <div class="card-actions">
          <button @click="refreshCache" class="action-btn primary" :disabled="refreshing">
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': refreshing }"></i>
            Refresh Status
          </button>
        </div>
      </div>
    </div>

    <!-- Class Cache Status -->
    <div class="cache-grid">
      <h2>Class Cache Status</h2>
      <div class="class-grid">
        <div 
          v-for="className in allClasses" 
          :key="className"
          class="class-card"
          :class="{ cached: isClassCached(className) }"
        >
          <div class="class-header">
            <div class="class-icon" :style="{ backgroundColor: getClassColor(className) }">
              <img 
                :src="`/icons/${className}.gif`" 
                :alt="className"
                @error="handleImageError"
              >
            </div>
            <h3>{{ formatClassName(className) }}</h3>
          </div>
          <div class="class-status">
            <div v-if="isClassCached(className)" class="cached-info">
              <div class="status-row">
                <i class="fas fa-check-circle"></i>
                <span>Cached</span>
              </div>
              <div class="cache-time">
                {{ formatCacheTime(getCacheTime(className)) }}
              </div>
              <div class="spell-count">
                {{ getSpellCount(className) || 0 }} spells
              </div>
            </div>
            <div v-else class="not-cached">
              <i class="fas fa-times-circle"></i>
              <span>Not Cached</span>
            </div>
          </div>
          <div class="class-actions">
            <button 
              @click="refreshClassCache(className)" 
              class="refresh-btn"
              :disabled="refreshingClass === className"
              title="Refresh this class"
            >
              <i class="fas fa-sync-alt" :class="{ 'fa-spin': refreshingClass === className }"></i>
            </button>
            <button 
              v-if="isClassCached(className)"
              @click="clearClassCache(className)" 
              class="clear-btn"
              title="Clear this class cache"
            >
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Cache Actions -->
    <div class="cache-actions-section">
      <h2>Cache Actions</h2>
      <div class="actions-grid">
        <div class="action-card">
          <h3>Save Cache to Disk</h3>
          <p>Persist current cache state to disk for faster startup</p>
          <button @click="saveCacheToDisk" class="action-btn success" :disabled="saving">
            <i class="fas fa-save" :class="{ 'fa-spin': saving }"></i>
            Save to Disk
          </button>
        </div>
        <div class="action-card">
          <h3>Clear All Caches</h3>
          <p>Remove all cached spell data from memory and disk</p>
          <button @click="clearAllCaches" class="action-btn danger" :disabled="clearing">
            <i class="fas fa-trash-alt" :class="{ 'fa-spin': clearing }"></i>
            Clear All Caches
          </button>
        </div>
        <div class="action-card">
          <h3>Refresh All Classes</h3>
          <p>Update cache for all classes with latest data</p>
          <button @click="refreshAllClasses" class="action-btn primary" :disabled="refreshingAll">
            <i class="fas fa-sync" :class="{ 'fa-spin': refreshingAll }"></i>
            Refresh All
          </button>
        </div>
      </div>
    </div>

    <!-- Cache Details -->
    <div v-if="Object.keys(cacheDetails).length > 0" class="cache-details">
      <h2>Cache Details</h2>
      <div class="details-content">
        <pre>{{ JSON.stringify(cacheDetails, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import { useSpellsStore } from '../stores/spells'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()
const spellsStore = useSpellsStore()

// API base URL
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 
  (import.meta.env.PROD ? 'https://eqdatascraper-backend-production.up.railway.app' : '')

// State
const cacheStatus = ref({})
const cacheDetails = ref({})
const refreshing = ref(false)
const refreshingClass = ref(null)
const refreshingAll = ref(false)
const saving = ref(false)
const clearing = ref(false)

// All EverQuest classes
const allClasses = [
  'bard', 'beastlord', 'berserker', 'cleric', 'druid', 'enchanter',
  'magician', 'monk', 'necromancer', 'paladin', 'ranger', 'rogue',
  'shadowknight', 'shaman', 'warrior', 'wizard'
]

// Computed
const cacheHealthClass = computed(() => {
  const cached = cacheStatus.value.total_cached || 0
  if (cached >= 14) return 'healthy'
  if (cached >= 8) return 'warning'
  return 'critical'
})

const cacheHealthText = computed(() => {
  const cached = cacheStatus.value.total_cached || 0
  if (cached >= 14) return 'Healthy'
  if (cached >= 8) return 'Partial'
  return 'Needs Update'
})

const cacheHealthIcon = computed(() => {
  const cached = cacheStatus.value.total_cached || 0
  if (cached >= 14) return 'fas fa-check-circle'
  if (cached >= 8) return 'fas fa-exclamation-triangle'
  return 'fas fa-times-circle'
})

// Methods
const loadCacheStatus = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/cache/status`)
    cacheStatus.value = response.data
    
    // Load detailed cache info
    const detailsResponse = await axios.get(`${API_BASE_URL}/api/cache-status`)
    cacheDetails.value = detailsResponse.data
  } catch (error) {
    console.error('Error loading cache status:', error)
  }
}

const refreshCache = async () => {
  refreshing.value = true
  try {
    await loadCacheStatus()
  } finally {
    refreshing.value = false
  }
}

const refreshClassCache = async (className) => {
  refreshingClass.value = className
  try {
    await axios.post(`${API_BASE_URL}/api/refresh-spell-cache/${className}`)
    await loadCacheStatus()
  } catch (error) {
    console.error(`Error refreshing ${className} cache:`, error)
  } finally {
    refreshingClass.value = null
  }
}

const refreshAllClasses = async () => {
  if (!confirm('This will refresh cache for all classes. This may take several minutes. Continue?')) {
    return
  }
  
  refreshingAll.value = true
  try {
    await axios.post(`${API_BASE_URL}/api/scrape-all`)
    await loadCacheStatus()
  } catch (error) {
    console.error('Error refreshing all classes:', error)
  } finally {
    refreshingAll.value = false
  }
}

const saveCacheToDisk = async () => {
  saving.value = true
  try {
    await axios.post(`${API_BASE_URL}/api/cache/save`)
    alert('Cache saved to disk successfully')
  } catch (error) {
    console.error('Error saving cache:', error)
    alert('Failed to save cache to disk')
  } finally {
    saving.value = false
  }
}

const clearAllCaches = async () => {
  if (!confirm('This will clear all cached data. Are you sure?')) {
    return
  }
  
  clearing.value = true
  try {
    await axios.post(`${API_BASE_URL}/api/cache/clear`)
    await loadCacheStatus()
    alert('All caches cleared successfully')
  } catch (error) {
    console.error('Error clearing caches:', error)
    alert('Failed to clear caches')
  } finally {
    clearing.value = false
  }
}

const clearClassCache = async (className) => {
  if (!confirm(`Clear cache for ${formatClassName(className)}?`)) {
    return
  }
  
  try {
    // Since there's no specific endpoint to clear a single class,
    // we'll need to implement this or use the general clear
    alert('Class-specific cache clearing not implemented yet')
  } catch (error) {
    console.error(`Error clearing ${className} cache:`, error)
  }
}

const isClassCached = (className) => {
  return cacheDetails.value[className]?.cached || false
}

const getCacheTime = (className) => {
  return cacheDetails.value[className]?.cache_time
}

const getSpellCount = (className) => {
  return cacheDetails.value[className]?.spell_count
}

const getClassColor = (className) => {
  const classObj = spellsStore.classes.find(c => c.apiName === className)
  return classObj?.color || '#667eea'
}

const formatClassName = (className) => {
  const classObj = spellsStore.classes.find(c => c.apiName === className)
  return classObj?.name || className.charAt(0).toUpperCase() + className.slice(1)
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

const formatCacheTime = (timestamp) => {
  if (!timestamp) return 'Unknown'
  return new Date(timestamp).toLocaleString()
}

const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const handleImageError = (event) => {
  event.target.style.display = 'none'
}

// Lifecycle
onMounted(() => {
  loadCacheStatus()
})
</script>

<style scoped>
.admin-cache {
  padding: 20px;
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

.cache-overview {
  margin-bottom: 40px;
}

.overview-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 30px;
  display: flex;
  align-items: center;
  gap: 30px;
}

.card-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 2.5rem;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
}

.card-content h3 {
  margin: 0 0 15px 0;
  font-size: 1.5rem;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 500;
  margin-bottom: 20px;
}

.status-indicator.healthy {
  background: #d4edda;
  color: #155724;
}

.status-indicator.warning {
  background: #fff3cd;
  color: #856404;
}

.status-indicator.critical {
  background: #f8d7da;
  color: #721c24;
}

.cache-stats {
  display: flex;
  gap: 30px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.stat .label {
  color: #666;
  font-size: 0.9rem;
}

.stat .value {
  font-weight: 600;
  font-size: 1.1rem;
  color: #1a202c;
}

.card-actions {
  display: flex;
  gap: 10px;
}

.action-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.action-btn.primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.action-btn.success {
  background: linear-gradient(135deg, #30cfd0 0%, #330867 100%);
  color: white;
}

.action-btn.danger {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cache-grid {
  margin-bottom: 40px;
}

.cache-grid h2 {
  margin-bottom: 20px;
}

.class-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.class-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 20px;
  transition: all 0.3s;
}

.class-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.class-card.cached {
  border: 2px solid #10b981;
}

.class-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 15px;
}

.class-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.class-icon img {
  width: 28px;
  height: 28px;
  object-fit: contain;
}

.class-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.class-status {
  margin-bottom: 15px;
  min-height: 60px;
}

.cached-info {
  color: #059669;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
}

.cache-time {
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 5px;
}

.spell-count {
  font-weight: 600;
}

.not-cached {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #dc2626;
}

.class-actions {
  display: flex;
  gap: 8px;
}

.refresh-btn,
.clear-btn {
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
}

.clear-btn:hover {
  border-color: #dc2626;
  color: #dc2626;
}

.cache-actions-section {
  margin-bottom: 40px;
}

.cache-actions-section h2 {
  margin-bottom: 20px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.action-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 25px;
  text-align: center;
}

.action-card h3 {
  margin: 0 0 10px 0;
  font-size: 1.2rem;
}

.action-card p {
  color: #666;
  margin-bottom: 20px;
}

.cache-details {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 25px;
}

.cache-details h2 {
  margin-bottom: 20px;
}

.details-content {
  background: #f7fafc;
  border-radius: 8px;
  padding: 20px;
  overflow-x: auto;
}

.details-content pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.85rem;
}

@media (max-width: 768px) {
  .overview-card {
    flex-direction: column;
    text-align: center;
  }

  .cache-stats {
    flex-direction: column;
    gap: 15px;
  }

  .class-grid {
    grid-template-columns: 1fr;
  }
}
</style>