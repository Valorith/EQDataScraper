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
        <div class="card-content">
          <div class="header-row">
            <h3>Cache Status</h3>
            <div class="status-indicator" :class="cacheHealthClass">
              <i :class="cacheHealthIcon"></i>
              {{ cacheHealthText }}
            </div>
          </div>
          <div class="cache-stats">
            <div class="stat">
              <span class="label">Total Cached</span>
              <span class="value">{{ cacheStatus.total_cached || 0 }} / 16</span>
            </div>
            <div class="stat">
              <span class="label">Cache Size</span>
              <span class="value">{{ formatBytes(cacheStatus.total_size || 0) }}</span>
            </div>
            <div class="stat">
              <span class="label">Last Update</span>
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
          <div class="class-card-content">
            <div class="class-info">
              <h3>{{ formatClassName(className) }}</h3>
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
            </div>
            <div class="class-icon">
              <img 
                :src="`/icons/${className}.gif`" 
                :alt="className"
                @error="handleImageError"
              >
            </div>
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

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import { useSpellsStore } from '../stores/spells'
import { API_BASE_URL, buildApiUrl, API_ENDPOINTS } from '../config/api'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()
const spellsStore = useSpellsStore()

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
    
    // Load detailed cache info
    const detailsResponse = await axios.get(`${API_BASE_URL}/api/cache-status`)
    cacheDetails.value = detailsResponse.data
    
    // Calculate total cached classes from the details
    let totalCached = 0
    let lastUpdate = null
    let mostRecentUpdate = null
    
    for (const [className, classData] of Object.entries(detailsResponse.data)) {
      if (className !== '_config' && classData.cached) {
        totalCached++
        // Find the most recent update time
        if (classData.last_updated) {
          const updateTime = new Date(classData.last_updated)
          if (!mostRecentUpdate || updateTime > mostRecentUpdate) {
            mostRecentUpdate = updateTime
            lastUpdate = classData.last_updated
          }
        }
      }
    }
    
    // If all classes are cached but no update time found, use current time
    // (likely means cache was just loaded from database on startup)
    if (totalCached > 0 && !lastUpdate) {
      lastUpdate = new Date().toISOString()
    }
    
    // Calculate total size from storage info
    let totalSize = 0
    if (response.data.storage?.file_sizes_bytes) {
      totalSize = Object.values(response.data.storage.file_sizes_bytes).reduce((sum, size) => sum + size, 0)
    } else if (response.data.storage?.tables) {
      // For database storage, estimate size based on row counts
      const tables = response.data.storage.tables
      // Rough estimation: average 1KB per spell, 500 bytes per pricing entry
      totalSize = (tables.spell_cache_rows || 0) * 1024 + 
                  (tables.pricing_cache_rows || 0) * 500 +
                  (tables.spell_details_cache_rows || 0) * 2048
    }
    
    // Update cache status with calculated values
    cacheStatus.value = {
      total_cached: totalCached,
      total_size: totalSize,
      last_update: lastUpdate,
      ...response.data
    }
    
    console.log('Cache status:', cacheStatus.value)
    console.log('Cache details:', cacheDetails.value)
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
  // Check both lowercase and proper case versions
  const titleCase = className.charAt(0).toUpperCase() + className.slice(1)
  
  // Special handling for compound names
  let properCase = titleCase
  if (className === 'shadowknight') properCase = 'ShadowKnight'
  else if (className === 'beastlord') properCase = 'BeastLord'
  
  return cacheDetails.value[className]?.cached || 
         cacheDetails.value[titleCase]?.cached || 
         cacheDetails.value[properCase]?.cached ||
         false
}

const getCacheTime = (className) => {
  // Check both lowercase and proper case versions
  const titleCase = className.charAt(0).toUpperCase() + className.slice(1)
  
  // Special handling for compound names
  let properCase = titleCase
  if (className === 'shadowknight') properCase = 'ShadowKnight'
  else if (className === 'beastlord') properCase = 'BeastLord'
  
  return cacheDetails.value[className]?.last_updated || 
         cacheDetails.value[titleCase]?.last_updated ||
         cacheDetails.value[properCase]?.last_updated ||
         cacheDetails.value[className]?.cache_time ||
         cacheDetails.value[titleCase]?.cache_time ||
         cacheDetails.value[properCase]?.cache_time
}

const getSpellCount = (className) => {
  // Check both lowercase and proper case versions
  const titleCase = className.charAt(0).toUpperCase() + className.slice(1)
  
  // Special handling for compound names
  let properCase = titleCase
  if (className === 'shadowknight') properCase = 'ShadowKnight'
  else if (className === 'beastlord') properCase = 'BeastLord'
  
  return cacheDetails.value[className]?.spell_count || 
         cacheDetails.value[titleCase]?.spell_count || 
         cacheDetails.value[properCase]?.spell_count ||
         0
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
  padding-top: 100px; /* Increased padding to prevent logo overlap */
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
}

/* Add subtle background pattern */
.admin-cache::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    radial-gradient(circle at 20% 80%, rgba(102, 126, 234, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(118, 75, 162, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(102, 126, 234, 0.02) 0%, transparent 50%);
  pointer-events: none;
  z-index: -1;
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
  color: #666;
  font-size: 1.1rem;
  margin: 0;
}

.cache-overview {
  margin-bottom: 40px;
}

.overview-card {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.9) 0%, rgba(45, 55, 72, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.card-icon {
  display: none; /* Remove the icon box */
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 25px;
  padding: 40px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.card-content h3 {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 700;
  color: #f7fafc;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  border-radius: 25px;
  font-weight: 600;
  font-size: 1.1rem;
  align-self: flex-start;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.status-indicator i {
  font-size: 1.2rem;
}

.status-indicator.healthy {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-indicator.warning {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.status-indicator.critical {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.cache-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 30px;
  background: rgba(0, 0, 0, 0.2);
  padding: 25px;
  border-radius: 15px;
  backdrop-filter: blur(10px);
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.stat .label {
  color: #9ca3af;
  font-size: 0.95rem;
  font-weight: 500;
}

.stat .value {
  font-weight: 700;
  font-size: 1.3rem;
  color: #f7fafc;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.card-actions {
  padding: 25px 40px;
  background: rgba(0, 0, 0, 0.15);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.action-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  text-transform: none;
  letter-spacing: 0.02em;
  position: relative;
  overflow: hidden;
}

.action-btn i {
  font-size: 1.1rem;
}

.action-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.2) 50%, transparent 100%);
  transition: left 0.5s;
}

.action-btn:hover::before {
  left: 100%;
}

.action-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.action-btn.primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

.action-btn.success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}

.action-btn.success:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.action-btn.danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
}

.action-btn.danger:hover:not(:disabled) {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cache-grid {
  margin-bottom: 40px;
}

.cache-grid h2 {
  margin-bottom: 24px;
  font-size: 1.8rem;
  font-weight: 700;
  color: #f7fafc;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.class-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.class-card {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.85) 0%, rgba(45, 55, 72, 0.85) 100%);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.class-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.12),
              0 0 0 1px rgba(255, 255, 255, 0.3) inset;
}

.class-card.cached {
  border: 2px solid rgba(16, 185, 129, 0.5);
  background: linear-gradient(135deg, rgba(6, 78, 59, 0.85) 0%, rgba(4, 120, 87, 0.85) 100%);
}

.class-card-content {
  display: flex;
  align-items: stretch;
  min-height: 140px;
}

.class-info {
  flex: 1;
  padding: 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.class-info h3 {
  margin: 0 0 16px 0;
  font-size: 1.5rem;
  font-weight: 800;
  color: #f7fafc;
  letter-spacing: 0.01em;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.class-icon {
  width: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: transparent;
}

.class-icon img {
  width: 110px;
  height: 110px;
  object-fit: contain;
  z-index: 1;
  position: relative;
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.3));
  transition: transform 0.3s ease;
}

.class-card:hover .class-icon img {
  transform: scale(1.1);
}

.class-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0.15;
  z-index: 0;
}

.class-status {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cached-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 1.05rem;
  color: #10b981;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.status-row i {
  font-size: 1.1rem;
}

.cache-time {
  font-size: 0.85rem;
  color: #9ca3af;
  font-weight: 500;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.spell-count {
  font-weight: 700;
  font-size: 1.25rem;
  color: #34d399;
  margin-top: 4px;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.not-cached {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ef4444;
  font-weight: 600;
  font-size: 1.05rem;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.not-cached i {
  font-size: 1.1rem;
}

/* Action buttons removed from class cards to clean up the UI */

.cache-actions-section {
  margin-bottom: 40px;
  padding: 40px;
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.5) 0%, rgba(45, 55, 72, 0.5) 100%);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2),
              0 0 0 1px rgba(255, 255, 255, 0.05) inset;
}

.cache-actions-section h2 {
  margin-bottom: 24px;
  font-size: 1.8rem;
  font-weight: 700;
  color: #f7fafc;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
}

.action-card {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.85) 0%, rgba(45, 55, 72, 0.85) 100%);
  backdrop-filter: blur(15px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 30px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.action-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, transparent 0%, rgba(255, 255, 255, 0.02) 100%);
  pointer-events: none;
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4),
              0 0 0 1px rgba(255, 255, 255, 0.15) inset;
  border-color: rgba(255, 255, 255, 0.2);
}

.action-card h3 {
  margin: 0 0 12px 0;
  font-size: 1.3rem;
  font-weight: 700;
  color: #f7fafc;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.action-card p {
  color: #9ca3af;
  margin-bottom: 25px;
  font-size: 0.95rem;
  line-height: 1.5;
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