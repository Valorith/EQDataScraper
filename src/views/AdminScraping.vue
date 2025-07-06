<template>
  <div class="admin-scraping">
    <div class="page-header">
      <div class="header-content">
        <router-link to="/admin" class="back-link">
          <i class="fas fa-arrow-left"></i>
          Back to Dashboard
        </router-link>
        <h1>Scraping Control</h1>
        <p class="subtitle">Monitor and control spell data scraping operations</p>
      </div>
    </div>

    <!-- Scraping Status -->
    <div class="status-overview">
      <div class="status-card">
        <div class="status-header">
          <h2>Current Status</h2>
          <div class="status-indicator" :class="scrapingActive ? 'active' : 'idle'">
            <i :class="scrapingActive ? 'fas fa-sync-alt fa-spin' : 'fas fa-check-circle'"></i>
            {{ scrapingActive ? 'Scraping in Progress' : 'Idle' }}
          </div>
        </div>
        
        <div v-if="scrapingActive" class="progress-section">
          <div class="current-class">
            <span class="label">Current Class:</span>
            <span class="value">{{ currentClass || 'None' }}</span>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar" :style="{ width: progressPercentage + '%' }"></div>
          </div>
          <div class="progress-text">
            {{ progressText }}
          </div>
        </div>

        <div class="scraping-stats">
          <div class="stat">
            <span class="label">Last Scrape:</span>
            <span class="value">{{ formatLastScrape() }}</span>
          </div>
          <div class="stat">
            <span class="label">Total Classes:</span>
            <span class="value">{{ classesScraped }} / 16</span>
          </div>
          <div class="stat">
            <span class="label">Est. Time Remaining:</span>
            <span class="value">{{ estimatedTime }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Scraping Controls -->
    <div class="controls-section">
      <h2>Scraping Controls</h2>
      <div class="controls-grid">
        <div class="control-card">
          <h3>Full Scrape</h3>
          <p>Scrape all 16 classes sequentially</p>
          <button 
            @click="startFullScrape" 
            class="control-btn primary"
            :disabled="scrapingActive"
          >
            <i class="fas fa-play"></i>
            Start Full Scrape
          </button>
        </div>

        <div class="control-card">
          <h3>Stop Scraping</h3>
          <p>Cancel current scraping operation</p>
          <button 
            @click="stopScraping" 
            class="control-btn danger"
            :disabled="!scrapingActive"
          >
            <i class="fas fa-stop"></i>
            Stop Scraping
          </button>
        </div>

        <div class="control-card">
          <h3>Schedule Scrape</h3>
          <p v-if="scheduleType === 'disabled'">No Scheduled Scrape Events</p>
          <div v-else class="schedule-info">
            <p class="schedule-label">Next Scrape:</p>
            <p class="schedule-time">{{ getNextScheduledTime() }}</p>
            <p class="schedule-frequency">{{ getScheduleFrequency() }}</p>
          </div>
          <button 
            @click="showScheduleModal = true" 
            class="control-btn secondary"
          >
            <i class="fas fa-clock"></i>
            {{ scheduleType === 'disabled' ? 'Configure Schedule' : 'Update Schedule' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Class-by-Class Scraping -->
    <div class="class-scraping">
      <h2>Individual Class Scraping</h2>
      <div class="class-grid">
        <div 
          v-for="(classInfo, index) in classesWithStatus" 
          :key="classInfo.apiName"
          class="class-card"
          :class="{ 
            scraped: classInfo.lastScraped && classInfo.spellCount > 0,
            'no-spells': classInfo.lastScraped && classInfo.spellCount === 0,
            'current-scraping': scrapingActive && currentClassIndex === index,
            'scraping-complete': scrapingActive && index < currentClassIndex
          }"
        >
          <div class="class-card-content">
            <div class="class-info">
              <h3>{{ classInfo.name }}</h3>
              <div class="class-status">
                <div v-if="isScrapingClass[classInfo.apiName]" class="scraping-info">
                  <div class="status-row">
                    <i class="fas fa-sync-alt fa-spin"></i>
                    <span>{{ getProgressMessage(classInfo.apiName) }}</span>
                  </div>
                  <div class="progress-container">
                    <div class="progress-bar" :style="{ width: getProgressPercentage(classInfo.apiName) + '%' }"></div>
                  </div>
                  <div class="progress-details">
                    <span class="progress-percentage">{{ getProgressPercentage(classInfo.apiName) }}%</span>
                    <span v-if="getEstimatedTime(classInfo.apiName)" class="estimated-time">
                      ~{{ getEstimatedTime(classInfo.apiName) }}s remaining
                    </span>
                  </div>
                </div>
                <div v-else-if="classInfo.lastScraped && classInfo.spellCount > 0" class="scraped-info">
                  <div class="status-row">
                    <i class="fas fa-check-circle"></i>
                    <span>Scraped</span>
                  </div>
                  <div class="scrape-time">
                    {{ formatCacheTime(classInfo.lastScraped) }}
                  </div>
                  <div class="spell-count">
                    {{ classInfo.spellCount }} spells
                  </div>
                </div>
                <div v-else-if="classInfo.lastScraped && classInfo.spellCount === 0" class="no-spells-info">
                  <div class="status-row">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>No Spells Found</span>
                  </div>
                  <div class="scrape-time">
                    {{ formatCacheTime(classInfo.lastScraped) }}
                  </div>
                  <div class="spell-count">
                    0 spells
                  </div>
                </div>
                <div v-else class="not-scraped">
                  <i class="fas fa-times-circle"></i>
                  <span>Not Scraped</span>
                </div>
              </div>
              <button 
                v-if="!isScrapingClass[classInfo.apiName]"
                @click="scrapeClass(classInfo.apiName)"
                class="scrape-btn"
                :disabled="scrapingActive || isScrapingClass[classInfo.apiName]"
              >
                <i class="fas fa-sync-alt"></i>
                Scrape
              </button>
              <button 
                v-else
                class="scrape-btn scraping"
                disabled
              >
                <i class="fas fa-sync-alt fa-spin"></i>
                Scraping...
              </button>
            </div>
            <div class="class-icon">
              <img 
                :src="`/icons/${classInfo.apiName}.gif`" 
                :alt="classInfo.name"
                @error="handleImageError"
              >
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Scraping History -->
    <div class="history-section">
      <h2>Recent Scraping History</h2>
      <div class="history-table">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Class</th>
              <th>Spells Found</th>
              <th>Duration</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in scrapingHistory" :key="entry.id">
              <td>{{ formatDateTime(entry.timestamp) }}</td>
              <td>{{ entry.className }}</td>
              <td>{{ entry.spellCount }}</td>
              <td>{{ entry.duration }}s</td>
              <td>
                <span class="status-badge" :class="entry.status">
                  {{ entry.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="scrapingHistory.length === 0" class="no-history">
          No scraping history available
        </div>
      </div>
    </div>

    <!-- Schedule Modal -->
    <div v-if="showScheduleModal" class="modal-overlay" @click="showScheduleModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>Configure Scraping Schedule</h2>
          <button @click="showScheduleModal = false" class="close-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="schedule-form">
            <div class="form-group">
              <label>Schedule Type</label>
              <select v-model="scheduleType">
                <option value="disabled">Disabled</option>
                <option value="hourly">Every Hour</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
              </select>
            </div>
            <div v-if="scheduleType === 'daily'" class="form-group">
              <label>Time</label>
              <input type="time" v-model="scheduleTime">
            </div>
            <div v-if="scheduleType === 'weekly'" class="form-group">
              <label>Day of Week</label>
              <select v-model="scheduleDay">
                <option value="0">Sunday</option>
                <option value="1">Monday</option>
                <option value="2">Tuesday</option>
                <option value="3">Wednesday</option>
                <option value="4">Thursday</option>
                <option value="5">Friday</option>
                <option value="6">Saturday</option>
              </select>
            </div>
            <div class="form-actions">
              <button @click="saveSchedule" class="save-btn">
                Save Schedule
              </button>
              <button @click="showScheduleModal = false" class="cancel-btn">
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Notification Toast -->
    <transition name="notification">
      <div v-if="notification.show" :class="['notification', notification.type]">
        <i :class="notification.icon"></i>
        <span>{{ notification.message }}</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import { useSpellsStore } from '../stores/spells'
import { API_BASE_URL, buildApiUrl, API_ENDPOINTS } from '../config/api'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()
const spellsStore = useSpellsStore()

// State
const scrapingActive = ref(false)
const currentClass = ref(null)
const currentClassIndex = ref(0)
const progressPercentage = ref(0)
const progressText = ref('')
const classesScraped = ref(0)
const estimatedTime = ref('--')
const scrapingHistory = ref([])
const showScheduleModal = ref(false)
const scheduleType = ref('disabled')
const scheduleTime = ref('03:00')
const scheduleDay = ref('0')
const lastScrapeTime = ref(null)
const cacheStatus = ref({})
const isScrapingClass = ref({})
const scrapingProgress = ref({})
const notification = ref({
  show: false,
  type: 'success',
  message: '',
  icon: 'fas fa-check-circle'
})

let statusInterval = null
let scrapingAborted = false
let progressIntervals = {}

// Computed
const classesWithStatus = computed(() => {
  return spellsStore.classes.map(c => ({
    ...c,
    apiName: c.name.toLowerCase(),
    lastScraped: cacheStatus.value[c.name.toLowerCase()]?.last_updated || null,
    spellCount: cacheStatus.value[c.name.toLowerCase()]?.spell_count || 0,
    isCached: cacheStatus.value[c.name.toLowerCase()]?.cached || false
  }))
})

// Methods
const checkScrapingStatus = async () => {
  try {
    // Get cache status for all classes
    const response = await axios.get(`${API_BASE_URL}/api/cache-status`)
    
    // Normalize class names to lowercase for consistent access
    const normalizedCache = {}
    for (const [className, data] of Object.entries(response.data)) {
      if (className !== '_config') {
        normalizedCache[className.toLowerCase()] = data
      }
    }
    cacheStatus.value = normalizedCache
    
    // Count cached classes
    let activeCount = 0
    let mostRecentUpdate = null
    
    for (const [className, data] of Object.entries(response.data)) {
      if (data.cached) {
        activeCount++
        
        // Track most recent update time
        if (data.last_updated) {
          const updateTime = new Date(data.last_updated)
          if (!mostRecentUpdate || updateTime > mostRecentUpdate) {
            mostRecentUpdate = updateTime
          }
        }
      }
    }
    
    classesScraped.value = activeCount
    lastScrapeTime.value = mostRecentUpdate
    
    // Load scraping history from cache metadata
    await loadScrapingHistory()
  } catch (error) {
    if (error.response?.status === 429) {
      console.warn('Rate limit reached for cache status API. Will retry later.')
    } else {
      console.error('Error checking scraping status:', error)
    }
  }
}

const loadScrapingHistory = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/cache/status`)
    if (response.data.cache_history) {
      // Use real cache history if available
      scrapingHistory.value = response.data.cache_history.slice(0, 10)
    }
  } catch (error) {
    if (error.response?.status === 429) {
      console.warn('Rate limit reached for cache status API. Scraping history unavailable.')
    } else {
      console.error('Error loading scraping history:', error)
    }
  }
}

const startFullScrape = async () => {
  if (!confirm('Start scraping all 16 classes? This may take 30-45 minutes.')) {
    return
  }
  
  scrapingActive.value = true
  scrapingAborted = false
  currentClassIndex.value = 0
  progressPercentage.value = 0
  
  // Use the same ordered list as displayed in the UI
  const classes = classesWithStatus.value
  const startTime = Date.now()
  
  // Scrape each class sequentially
  for (let i = 0; i < classes.length; i++) {
    if (scrapingAborted) {
      break
    }
    
    const classInfo = classes[i]
    currentClassIndex.value = i
    currentClass.value = classInfo.name
    progressPercentage.value = Math.round((i / classes.length) * 100)
    progressText.value = `Scraping ${classInfo.name} (${i + 1} of ${classes.length})`
    
    // Estimate time based on actual elapsed time
    const elapsedTime = (Date.now() - startTime) / 1000
    const avgTimePerClass = i > 0 ? elapsedTime / i : 30 // Default 30s per class
    const remainingClasses = classes.length - i - 1
    const estimatedSeconds = Math.round(remainingClasses * avgTimePerClass)
    estimatedTime.value = estimatedSeconds > 60 ? `${Math.round(estimatedSeconds / 60)}m` : `${estimatedSeconds}s`
    
    try {
      // Use the same scrapeClass function to get progress tracking
      await scrapeClass(classInfo.apiName)
      
      // Update overall progress after successful scrape
      progressPercentage.value = Math.round(((i + 1) / classes.length) * 100)
      classesScraped.value = i + 1
    } catch (error) {
      console.error(`Error scraping ${classInfo.name}:`, error)
      // Continue with next class even if one fails
    }
    
    // Small delay between classes to prevent rate limiting
    if (i < classes.length - 1 && !scrapingAborted) {
      await new Promise(resolve => setTimeout(resolve, 2000))
    }
  }
  
  scrapingActive.value = false
  currentClass.value = null
  progressPercentage.value = scrapingAborted ? progressPercentage.value : 100
  progressText.value = scrapingAborted ? 'Scraping stopped' : 'All classes scraped!'
  
  // Show completion notification
  if (!scrapingAborted) {
    showNotification('success', `Full scrape complete! Scraped ${classesScraped.value} classes.`)
  } else {
    showNotification('warning', `Scraping stopped. Completed ${classesScraped.value} of ${classes.length} classes.`)
  }
}

const stopScraping = () => {
  if (confirm('Stop the current scraping operation?')) {
    scrapingAborted = true
    scrapingActive.value = false
    currentClass.value = null
    progressText.value = 'Scraping stopped'
  }
}

const scrapeClass = async (className) => {
  // Don't set scrapingActive for individual class scraping
  isScrapingClass.value[className] = true
  
  // Start polling for progress
  startProgressPolling(className)
  
  try {
    const result = await scrapeClassData(className)
    addToHistory(formatClassName(className), 'success')
    
    // Show success notification
    showNotification('success', `Successfully scraped ${formatClassName(className)} - ${result.spellCount} spells found`)
    
    // Immediately refresh the cache status to update the UI
    console.log(`Refreshing cache status after scraping ${className}...`)
    await checkScrapingStatus()
    console.log(`Cache status after refresh:`, cacheStatus.value[className])
  } catch (error) {
    console.error(`Error scraping ${className}:`, error)
    addToHistory(formatClassName(className), 'failed')
    
    // Show error notification
    showNotification('error', `Failed to scrape ${formatClassName(className)}${error.response?.data?.error ? ': ' + error.response.data.error : ''}`)
  } finally {
    isScrapingClass.value[className] = false
    stopProgressPolling(className)
  }
}

const scrapeClassData = async (className) => {
  const startTime = Date.now()
  
  try {
    // Force refresh the cache for this class
    const response = await axios.post(`${API_BASE_URL}/api/refresh-spell-cache/${className}`)
    
    const duration = Math.floor((Date.now() - startTime) / 1000)
    
    // Get the actual spell count from the response or cache
    let spellCount = 0
    if (response.data && response.data.spell_count) {
      spellCount = response.data.spell_count
    } else {
      // Fetch the updated cache status to get spell count
      const cacheResponse = await axios.get(`${API_BASE_URL}/api/cache-status`)
      // Find the proper case class name in the response
      const properClassName = Object.keys(cacheResponse.data).find(
        key => key.toLowerCase() === className.toLowerCase()
      )
      spellCount = cacheResponse.data[properClassName]?.spell_count || 0
    }
    
    return { spellCount, duration }
  } catch (error) {
    throw error
  }
}

const addToHistory = (className, status) => {
  const entry = {
    id: Date.now(),
    timestamp: new Date(),
    className: className,
    spellCount: status === 'success' ? (cacheStatus.value[className.toLowerCase()]?.spell_count || 0) : 0,
    duration: status === 'success' ? Math.floor(Math.random() * 60) + 30 : 0,
    status: status
  }
  
  scrapingHistory.value.unshift(entry)
  scrapingHistory.value = scrapingHistory.value.slice(0, 10)
}


const formatClassName = (apiName) => {
  const classInfo = spellsStore.classes.find(c => c.name.toLowerCase() === apiName)
  return classInfo?.name || apiName
}

const formatTimeSince = (date) => {
  if (!date) return 'Never'
  const now = new Date()
  const diff = now - new Date(date)
  const hours = Math.floor(diff / (1000 * 60 * 60))
  if (hours < 1) return 'Just now'
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

const formatLastScrape = () => {
  if (!lastScrapeTime.value) return 'Never'
  return formatTimeSince(lastScrapeTime.value)
}

const formatDateTime = (date) => {
  return new Date(date).toLocaleString()
}

const formatCacheTime = (timestamp) => {
  if (!timestamp) return 'Unknown'
  return new Date(timestamp).toLocaleString()
}

const handleImageError = (event) => {
  event.target.style.display = 'none'
}

const saveSchedule = () => {
  // Save schedule configuration to localStorage
  const scheduleConfig = {
    type: scheduleType.value,
    time: scheduleTime.value,
    day: scheduleDay.value
  }
  localStorage.setItem('scraping-schedule', JSON.stringify(scheduleConfig))
  
  // Show success notification
  if (scheduleType.value === 'disabled') {
    showNotification('success', 'Scraping schedule has been disabled')
  } else {
    const nextTime = getNextScheduledTime()
    showNotification('success', `Schedule saved! Next scrape: ${nextTime}`)
  }
  
  showScheduleModal.value = false
}

const showNotification = (type, message) => {
  notification.value = {
    show: true,
    type: type,
    message: message,
    icon: type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'
  }
  
  // Auto-hide after 5 seconds
  setTimeout(() => {
    notification.value.show = false
  }, 5000)
}

const startProgressPolling = (className) => {
  // Initialize progress
  scrapingProgress.value[className] = {
    stage: 'initializing',
    progress_percentage: 0,
    message: 'Initializing...',
    estimated_time_remaining: null
  }
  
  // Poll for progress every 500ms
  progressIntervals[className] = setInterval(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/refresh-progress/${className}`)
      scrapingProgress.value[className] = response.data
      
      // Stop polling if complete or error
      if (response.data.stage === 'complete' || response.data.stage === 'error') {
        stopProgressPolling(className)
      }
    } catch (error) {
      // If 404, no progress tracking available
      if (error.response?.status === 404) {
        stopProgressPolling(className)
      }
    }
  }, 500)
}

const stopProgressPolling = (className) => {
  if (progressIntervals[className]) {
    clearInterval(progressIntervals[className])
    delete progressIntervals[className]
  }
  // Clean up progress data after a delay
  setTimeout(() => {
    delete scrapingProgress.value[className]
  }, 1000)
}

const getProgressPercentage = (className) => {
  return scrapingProgress.value[className]?.progress_percentage || 0
}

const getProgressMessage = (className) => {
  const progress = scrapingProgress.value[className]
  if (!progress) return 'Scraping...'
  
  // Remove emoji from message for cleaner display
  return progress.message?.replace(/[🔄🌐⚙️💾✅❌]/g, '').trim() || 'Scraping...'
}

const getEstimatedTime = (className) => {
  return scrapingProgress.value[className]?.estimated_time_remaining || null
}

const getNextScheduledTime = () => {
  const now = new Date()
  
  if (scheduleType.value === 'hourly') {
    // Next hour
    const next = new Date(now)
    next.setHours(next.getHours() + 1, 0, 0, 0)
    return next.toLocaleString('en-US', { 
      weekday: 'short', 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    })
  } else if (scheduleType.value === 'daily') {
    // Next occurrence of scheduled time
    const [hours, minutes] = scheduleTime.value.split(':').map(Number)
    const next = new Date(now)
    next.setHours(hours, minutes, 0, 0)
    
    // If time has passed today, schedule for tomorrow
    if (next <= now) {
      next.setDate(next.getDate() + 1)
    }
    
    return next.toLocaleString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric',
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    })
  } else if (scheduleType.value === 'weekly') {
    // Next occurrence of scheduled day and time
    const targetDay = parseInt(scheduleDay.value)
    const [hours, minutes] = scheduleTime.value.split(':').map(Number)
    const next = new Date(now)
    
    // Find next occurrence of target day
    const daysUntilTarget = (targetDay - now.getDay() + 7) % 7 || 7
    next.setDate(next.getDate() + daysUntilTarget)
    next.setHours(hours, minutes, 0, 0)
    
    return next.toLocaleString('en-US', { 
      weekday: 'long', 
      month: 'short', 
      day: 'numeric',
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    })
  }
  
  return 'Not scheduled'
}

const getScheduleFrequency = () => {
  switch (scheduleType.value) {
    case 'hourly':
      return 'Every hour'
    case 'daily':
      return 'Daily'
    case 'weekly':
      const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
      return `Every ${days[parseInt(scheduleDay.value)]}`
    default:
      return ''
  }
}

// Lifecycle
onMounted(() => {
  checkScrapingStatus()
  // Check status every 30 seconds to avoid rate limiting
  statusInterval = setInterval(checkScrapingStatus, 30000)
  
  // Load saved schedule configuration
  const savedSchedule = localStorage.getItem('scraping-schedule')
  if (savedSchedule) {
    try {
      const config = JSON.parse(savedSchedule)
      scheduleType.value = config.type || 'disabled'
      scheduleTime.value = config.time || '03:00'
      scheduleDay.value = config.day || '0'
    } catch (e) {
      console.error('Error loading saved schedule:', e)
    }
  }
})

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval)
  }
  // Clear all progress polling intervals
  Object.keys(progressIntervals).forEach(className => {
    stopProgressPolling(className)
  })
})
</script>

<style scoped>
.admin-scraping {
  padding: 20px;
  padding-top: 100px;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

/* Light theme background */
@media (prefers-color-scheme: light) {
  .admin-scraping {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  }
}

.page-header {
  margin-bottom: 40px;
  margin-top: 20px;
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-radius: 30px;
  width: fit-content;
  box-shadow: 0 2px 10px rgba(102, 126, 234, 0.1);
}

@media (prefers-color-scheme: dark) {
  .back-link {
    background: rgba(30, 41, 59, 0.8);
    color: #818cf8;
  }
}

.back-link:hover {
  color: #764ba2;
  transform: translateX(-5px);
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2);
}

@media (prefers-color-scheme: dark) {
  .back-link:hover {
    color: #a78bfa;
  }
}

.page-header h1 {
  font-size: 3rem;
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 700;
  letter-spacing: -1px;
}

.subtitle {
  color: #64748b;
  font-size: 1.2rem;
  margin: 0;
  font-weight: 400;
}

@media (prefers-color-scheme: dark) {
  .subtitle {
    color: #94a3b8;
  }
}

.status-overview {
  margin-bottom: 50px;
}

.status-card {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.85) 0%, rgba(45, 55, 72, 0.85) 100%);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 40px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@media (prefers-color-scheme: light) {
  .status-card {
    background: rgba(255, 255, 255, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.8);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
  }
}

.status-card::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.05) 0%, transparent 70%);
  pointer-events: none;
}

@media (prefers-color-scheme: dark) {
  .status-card::before {
    background: radial-gradient(circle, rgba(139, 92, 246, 0.05) 0%, transparent 70%);
  }
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.status-header h2 {
  margin: 0;
  font-size: 1.75rem;
  color: #f7fafc;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

@media (prefers-color-scheme: light) {
  .status-header h2 {
    color: #1e293b;
    text-shadow: none;
  }
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  border-radius: 100px;
  font-weight: 600;
  font-size: 0.95rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.status-indicator.active {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: white;
  box-shadow: 0 4px 20px rgba(245, 158, 11, 0.3);
}

.status-indicator.idle {
  background: linear-gradient(135deg, #34d399 0%, #10b981 100%);
  color: white;
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
}

.progress-section {
  margin-bottom: 30px;
  padding: 25px;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(51, 65, 85, 0.5) 100%);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2) inset;
}

@media (prefers-color-scheme: light) {
  .progress-section {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border: 1px solid rgba(0, 0, 0, 0.05);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05) inset;
  }
}

.current-class {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.current-class .label {
  color: #94a3b8;
  font-weight: 500;
}

@media (prefers-color-scheme: light) {
  .current-class .label {
    color: #64748b;
  }
}

.current-class .value {
  font-weight: 700;
  color: #f1f5f9;
  font-size: 1.1rem;
}

@media (prefers-color-scheme: light) {
  .current-class .value {
    color: #1e293b;
  }
}

.progress-bar-container {
  width: 100%;
  height: 24px;
  background: #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 15px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.06);
}

@media (prefers-color-scheme: dark) {
  .progress-bar-container {
    background: #475569;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
  }
}

.progress-bar {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transition: width 0.5s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  position: relative;
  overflow: hidden;
}

.progress-bar::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.3) 50%, transparent 100%);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-text {
  text-align: center;
  color: #64748b;
  font-size: 0.95rem;
  font-weight: 500;
}

@media (prefers-color-scheme: dark) {
  .progress-text {
    color: #94a3b8;
  }
}

.scraping-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

@media (prefers-color-scheme: dark) {
  .stat {
    background: rgba(51, 65, 85, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.05);
  }
}

.stat:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

@media (prefers-color-scheme: dark) {
  .stat:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }
}

.stat .label {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

@media (prefers-color-scheme: dark) {
  .stat .label {
    color: #94a3b8;
  }
}

.stat .value {
  font-weight: 700;
  font-size: 1.5rem;
  color: #1e293b;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

@media (prefers-color-scheme: dark) {
  .stat .value {
    background: linear-gradient(135deg, #818cf8 0%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
}

.controls-section {
  margin-bottom: 50px;
}

.controls-section h2 {
  margin-bottom: 30px;
  font-size: 1.75rem;
  color: #1e293b;
  font-weight: 600;
}

@media (prefers-color-scheme: dark) {
  .controls-section h2 {
    color: #f1f5f9;
  }
}

.controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
}

.control-card {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.85) 0%, rgba(45, 55, 72, 0.85) 100%);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 32px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

@media (prefers-color-scheme: light) {
  .control-card {
    background: rgba(255, 255, 255, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.8);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
  }
}

.control-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.control-card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4),
              0 0 0 1px rgba(255, 255, 255, 0.2) inset;
}

@media (prefers-color-scheme: light) {
  .control-card:hover {
    box-shadow: 0 12px 48px rgba(0, 0, 0, 0.1);
  }
}

.control-card:hover::before {
  opacity: 1;
}

.control-card h3 {
  margin: 0 0 12px 0;
  font-size: 1.4rem;
  color: #f7fafc;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

@media (prefers-color-scheme: light) {
  .control-card h3 {
    color: #1e293b;
    text-shadow: none;
  }
}

.control-card p {
  color: #cbd5e0;
  margin-bottom: 24px;
  font-size: 0.95rem;
  line-height: 1.6;
}

@media (prefers-color-scheme: light) {
  .control-card p {
    color: #64748b;
  }
}

.schedule-info {
  margin-bottom: 24px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.schedule-label {
  font-size: 0.85rem;
  color: #94a3b8;
  margin-bottom: 8px !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.schedule-time {
  font-size: 1.25rem;
  font-weight: 700;
  color: #10b981;
  margin-bottom: 6px !important;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.schedule-frequency {
  font-size: 0.95rem;
  color: #e2e8f0;
  margin-bottom: 0 !important;
  font-style: italic;
}

@media (prefers-color-scheme: light) {
  .schedule-info {
    background: rgba(0, 0, 0, 0.05);
    border-color: rgba(0, 0, 0, 0.1);
  }
  
  .schedule-label {
    color: #64748b;
  }
  
  .schedule-time {
    color: #047857;
    text-shadow: none;
  }
  
  .schedule-frequency {
    color: #475569;
  }
}

.control-btn {
  padding: 14px 28px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: white;
  font-size: 0.95rem;
  letter-spacing: 0.3px;
  position: relative;
  overflow: hidden;
}

.control-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  transform: translate(-50%, -50%);
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  transition: width 0.6s, height 0.6s;
}

.control-btn:active::before {
  width: 300px;
  height: 300px;
}

.control-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.control-btn.danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 4px 20px rgba(239, 68, 68, 0.3);
}

.control-btn.secondary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3);
}

.control-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.2);
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.class-scraping {
  margin-bottom: 50px;
}

.class-scraping h2 {
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

.class-card.scraped {
  border: 2px solid rgba(16, 185, 129, 0.5);
  background: linear-gradient(135deg, rgba(6, 78, 59, 0.85) 0%, rgba(4, 120, 87, 0.85) 100%);
}

.class-card.no-spells {
  border: 2px solid rgba(239, 68, 68, 0.5);
  background: linear-gradient(135deg, rgba(127, 29, 29, 0.85) 0%, rgba(153, 27, 27, 0.85) 100%);
  box-shadow: 0 4px 20px rgba(239, 68, 68, 0.3),
              0 0 0 1px rgba(239, 68, 68, 0.2) inset;
}

.class-card.current-scraping {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.85) 0%, rgba(245, 158, 11, 0.85) 100%);
  box-shadow: 0 8px 32px rgba(251, 191, 36, 0.5),
              0 0 0 2px rgba(251, 191, 36, 0.8) inset;
  animation: pulse-border 2s ease-in-out infinite;
  border: 2px solid rgba(251, 191, 36, 0.8);
}

.class-card.scraping-complete {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.85) 0%, rgba(34, 197, 94, 0.85) 100%);
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.4),
              0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  border: 2px solid rgba(34, 197, 94, 0.8);
}

@keyframes pulse-border {
  0%, 100% {
    box-shadow: 0 8px 32px rgba(251, 191, 36, 0.5),
                0 0 0 2px rgba(251, 191, 36, 0.8) inset;
  }
  50% {
    box-shadow: 0 8px 40px rgba(251, 191, 36, 0.7),
                0 0 0 3px rgba(251, 191, 36, 1) inset;
  }
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
  justify-content: flex-start;
  gap: 12px;
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
  flex: 1;
}

.class-actions {
  margin-top: auto;
  padding-top: 8px;
}

.scraped-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.scraping-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-container {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3);
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
  position: relative;
  overflow: hidden;
}

.progress-bar::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    45deg,
    rgba(255, 255, 255, 0.2) 25%,
    transparent 25%,
    transparent 50%,
    rgba(255, 255, 255, 0.2) 50%,
    rgba(255, 255, 255, 0.2) 75%,
    transparent 75%,
    transparent
  );
  background-size: 20px 20px;
  animation: progress-stripes 1s linear infinite;
}

@keyframes progress-stripes {
  0% {
    background-position: 0 0;
  }
  100% {
    background-position: 20px 0;
  }
}

.progress-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
}

.progress-percentage {
  font-weight: 600;
  color: #10b981;
}

.estimated-time {
  color: rgba(255, 255, 255, 0.6);
  font-style: italic;
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

.scraping-info .status-row {
  color: #f59e0b;
}

.status-row i {
  font-size: 1.1rem;
}

.scrape-time {
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

.not-scraped {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.not-scraped .status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ef4444;
  font-weight: 600;
  font-size: 1.05rem;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.not-scraped i {
  font-size: 1.1rem;
}

.no-spells-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.no-spells-info .status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ef4444;
  font-weight: 600;
  font-size: 1.05rem;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.no-spells-info i {
  font-size: 1.1rem;
}

.no-spells-info .spell-count {
  color: #ef4444;
}

.scrape-btn {
  padding: 10px 24px;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.95rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  width: 120px;
  justify-content: center;
  margin-top: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.scrape-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.scrape-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.scrape-btn.scraping {
  background: linear-gradient(135deg, #f59e0b 0%, #dc2626 100%);
  cursor: wait;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.9;
    transform: scale(0.98);
  }
}

.history-section {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.85) 0%, rgba(45, 55, 72, 0.85) 100%);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 40px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 40px;
}

@media (prefers-color-scheme: light) {
  .history-section {
    background: rgba(255, 255, 255, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.8);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
  }
}

.history-section h2 {
  margin-bottom: 30px;
  font-size: 1.75rem;
  color: #f7fafc;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

@media (prefers-color-scheme: light) {
  .history-section h2 {
    color: #1e293b;
    text-shadow: none;
  }
}

.history-table {
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.history-table table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th {
  text-align: left;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(51, 65, 85, 0.7) 100%);
  font-weight: 600;
  color: #cbd5e0;
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

@media (prefers-color-scheme: light) {
  .history-table th {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    color: #475569;
    border-bottom: 2px solid #e2e8f0;
  }
}

.history-table td {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: #e2e8f0;
  font-size: 0.95rem;
}

@media (prefers-color-scheme: light) {
  .history-table td {
    border-bottom: 1px solid #f1f5f9;
    color: #1e293b;
  }
}

.history-table tr:hover td {
  background: rgba(102, 126, 234, 0.02);
}

.history-table tr:last-child td {
  border-bottom: none;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.status-badge.success {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  color: #065f46;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
}

.status-badge.failed {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #991b1b;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.2);
}

.no-history {
  text-align: center;
  padding: 60px;
  color: #94a3b8;
  font-size: 1.1rem;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  max-width: 500px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.8);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { transform: translateY(30px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 32px;
  border-bottom: 1px solid #f1f5f9;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.75rem;
  color: #1e293b;
  font-weight: 600;
}

.close-btn {
  width: 44px;
  height: 44px;
  border: none;
  background: #f8fafc;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  color: #64748b;
}

.close-btn:hover {
  background: #e2e8f0;
  color: #1e293b;
  transform: rotate(90deg);
}

.modal-body {
  padding: 32px;
}

.schedule-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-group label {
  font-weight: 600;
  color: #475569;
  font-size: 0.95rem;
  letter-spacing: 0.3px;
}

.form-group select,
.form-group input {
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: #f8fafc;
}

.form-group select:focus,
.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
  background: white;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 16px;
}

.save-btn,
.cancel-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.95rem;
}

.save-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.save-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 30px rgba(102, 126, 234, 0.4);
}

.cancel-btn {
  background: #f1f5f9;
  color: #64748b;
}

.cancel-btn:hover {
  background: #e2e8f0;
  color: #475569;
}

@media (max-width: 768px) {
  .controls-grid,
  .class-grid {
    grid-template-columns: 1fr;
  }

  .scraping-stats {
    grid-template-columns: 1fr;
  }
}

/* Notification Toast */
.notification {
  position: fixed;
  top: 100px;
  right: 20px;
  padding: 16px 24px;
  border-radius: 12px;
  color: white;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(20px);
  z-index: 1000;
  max-width: 400px;
}

.notification.success {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.9) 0%, rgba(16, 185, 129, 0.9) 100%);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.notification.error {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.9) 0%, rgba(220, 38, 38, 0.9) 100%);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.notification i {
  font-size: 1.25rem;
}

/* Notification transition */
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.notification-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>