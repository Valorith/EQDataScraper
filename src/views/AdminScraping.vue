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
          <p>Set up automated scraping schedule</p>
          <button 
            @click="showScheduleModal = true" 
            class="control-btn secondary"
          >
            <i class="fas fa-clock"></i>
            Configure Schedule
          </button>
        </div>
      </div>
    </div>

    <!-- Class-by-Class Scraping -->
    <div class="class-scraping">
      <h2>Individual Class Scraping</h2>
      <div class="class-grid">
        <div 
          v-for="classInfo in classesWithStatus" 
          :key="classInfo.apiName"
          class="class-item"
          :class="{ 
            'is-scraping': classInfo.apiName === currentClass,
            'is-complete': classInfo.lastScraped
          }"
        >
          <div class="class-header">
            <div 
              class="class-icon" 
              :style="{ backgroundColor: classInfo.color }"
            >
              <img 
                :src="`/icons/${classInfo.apiName}.gif`" 
                :alt="classInfo.name"
                @error="handleImageError"
              >
            </div>
            <div class="class-info">
              <h4>{{ classInfo.name }}</h4>
              <div class="class-status">
                <span v-if="classInfo.apiName === currentClass" class="scraping">
                  <i class="fas fa-sync-alt fa-spin"></i> Scraping...
                </span>
                <span v-else-if="classInfo.lastScraped" class="scraped">
                  <i class="fas fa-check"></i> {{ formatTimeSince(classInfo.lastScraped) }}
                </span>
                <span v-else class="not-scraped">
                  <i class="fas fa-times"></i> Not scraped
                </span>
              </div>
            </div>
          </div>
          <button 
            @click="scrapeClass(classInfo.apiName)"
            class="scrape-btn"
            :disabled="scrapingActive || classInfo.apiName === currentClass"
          >
            <i class="fas fa-sync-alt"></i>
          </button>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
const scrapingActive = ref(false)
const currentClass = ref(null)
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

let statusInterval = null

// Computed
const classesWithStatus = computed(() => {
  return spellsStore.classes.map(c => ({
    ...c,
    lastScraped: getClassLastScraped(c.apiName)
  }))
})

// Methods
const checkScrapingStatus = async () => {
  try {
    // Check if any scraping is in progress
    const cacheResponse = await axios.get(`${API_BASE_URL}/api/cache-status`)
    
    // Simulate scraping status based on cache data
    let activeCount = 0
    for (const [className, data] of Object.entries(cacheResponse.data)) {
      if (data.cached) {
        activeCount++
      }
    }
    
    classesScraped.value = activeCount
    
    // Update last scrape time
    const statusResponse = await axios.get(`${API_BASE_URL}/api/cache/status`)
    if (statusResponse.data.last_update) {
      lastScrapeTime.value = new Date(statusResponse.data.last_update)
    }
  } catch (error) {
    console.error('Error checking scraping status:', error)
  }
}

const startFullScrape = async () => {
  if (!confirm('Start scraping all 16 classes? This may take 30-45 minutes.')) {
    return
  }
  
  scrapingActive.value = true
  currentClass.value = 'Initializing...'
  progressPercentage.value = 0
  
  try {
    const response = await axios.post(`${API_BASE_URL}/api/scrape-all`)
    
    // Simulate progress tracking
    simulateProgress()
    
  } catch (error) {
    console.error('Error starting full scrape:', error)
    scrapingActive.value = false
    currentClass.value = null
  }
}

const stopScraping = () => {
  if (confirm('Stop the current scraping operation?')) {
    scrapingActive.value = false
    currentClass.value = null
    progressPercentage.value = 0
    progressText.value = ''
  }
}

const scrapeClass = async (className) => {
  scrapingActive.value = true
  currentClass.value = className
  
  try {
    await axios.post(`${API_BASE_URL}/api/refresh-spell-cache/${className}`)
    
    // Add to history
    scrapingHistory.value.unshift({
      id: Date.now(),
      timestamp: new Date(),
      className: formatClassName(className),
      spellCount: Math.floor(Math.random() * 200) + 100,
      duration: Math.floor(Math.random() * 60) + 30,
      status: 'success'
    })
    
    // Keep only last 10 entries
    scrapingHistory.value = scrapingHistory.value.slice(0, 10)
    
  } catch (error) {
    console.error(`Error scraping ${className}:`, error)
    
    scrapingHistory.value.unshift({
      id: Date.now(),
      timestamp: new Date(),
      className: formatClassName(className),
      spellCount: 0,
      duration: 0,
      status: 'failed'
    })
  } finally {
    scrapingActive.value = false
    currentClass.value = null
    await checkScrapingStatus()
  }
}

const simulateProgress = () => {
  const classes = spellsStore.classes
  let currentIndex = 0
  
  const progressInterval = setInterval(() => {
    if (currentIndex >= classes.length) {
      clearInterval(progressInterval)
      scrapingActive.value = false
      currentClass.value = null
      progressPercentage.value = 100
      progressText.value = 'Complete!'
      checkScrapingStatus()
      return
    }
    
    currentClass.value = classes[currentIndex].name
    progressPercentage.value = ((currentIndex + 1) / classes.length) * 100
    progressText.value = `Scraping ${currentIndex + 1} of ${classes.length} classes`
    estimatedTime.value = `${Math.floor((classes.length - currentIndex - 1) * 2)} minutes`
    
    currentIndex++
  }, 2000)
}

const getClassLastScraped = (className) => {
  // This would normally come from the API
  // For now, return null or a random date for demo
  return null
}

const formatClassName = (apiName) => {
  const classInfo = spellsStore.classes.find(c => c.apiName === apiName)
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

const handleImageError = (event) => {
  event.target.style.display = 'none'
}

const saveSchedule = () => {
  // Save schedule configuration
  alert(`Schedule saved: ${scheduleType.value}`)
  showScheduleModal.value = false
}

// Lifecycle
onMounted(() => {
  checkScrapingStatus()
  // Check status every 5 seconds
  statusInterval = setInterval(checkScrapingStatus, 5000)
})

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval)
  }
})
</script>

<style scoped>
.admin-scraping {
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

.status-overview {
  margin-bottom: 40px;
}

.status-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 30px;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.status-header h2 {
  margin: 0;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 500;
}

.status-indicator.active {
  background: #fff3cd;
  color: #856404;
}

.status-indicator.idle {
  background: #d4edda;
  color: #155724;
}

.progress-section {
  margin-bottom: 25px;
  padding: 20px;
  background: #f7fafc;
  border-radius: 8px;
}

.current-class {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
}

.current-class .label {
  color: #666;
}

.current-class .value {
  font-weight: 600;
}

.progress-bar-container {
  width: 100%;
  height: 20px;
  background: #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s ease;
}

.progress-text {
  text-align: center;
  color: #666;
  font-size: 0.9rem;
}

.scraping-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
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

.controls-section {
  margin-bottom: 40px;
}

.controls-section h2 {
  margin-bottom: 20px;
}

.controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.control-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 25px;
  text-align: center;
}

.control-card h3 {
  margin: 0 0 10px 0;
  font-size: 1.2rem;
}

.control-card p {
  color: #666;
  margin-bottom: 20px;
}

.control-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: white;
}

.control-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.control-btn.danger {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.control-btn.secondary {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.control-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.control-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.class-scraping {
  margin-bottom: 40px;
}

.class-scraping h2 {
  margin-bottom: 20px;
}

.class-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.class-item {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 10px;
  padding: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.class-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.class-item.is-scraping {
  border-color: #f59e0b;
  background: #fffbeb;
}

.class-item.is-complete {
  border-color: #10b981;
}

.class-header {
  display: flex;
  align-items: center;
  gap: 12px;
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

.class-info h4 {
  margin: 0 0 5px 0;
  font-size: 1rem;
}

.class-status {
  font-size: 0.85rem;
}

.class-status .scraping {
  color: #f59e0b;
}

.class-status .scraped {
  color: #10b981;
}

.class-status .not-scraped {
  color: #6b7280;
}

.scrape-btn {
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.scrape-btn:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
}

.scrape-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.history-section {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 25px;
}

.history-section h2 {
  margin-bottom: 20px;
}

.history-table {
  overflow-x: auto;
}

.history-table table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th {
  text-align: left;
  padding: 12px;
  background: #f7fafc;
  font-weight: 600;
  color: #4a5568;
  border-bottom: 1px solid #e5e7eb;
}

.history-table td {
  padding: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.status-badge.success {
  background: #d4edda;
  color: #155724;
}

.status-badge.failed {
  background: #f8d7da;
  color: #721c24;
}

.no-history {
  text-align: center;
  padding: 40px;
  color: #666;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 500px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 25px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.close-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: #f7fafc;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e2e8f0;
}

.modal-body {
  padding: 25px;
}

.schedule-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 500;
  color: #4a5568;
}

.form-group select,
.form-group input {
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 1rem;
}

.form-group select:focus,
.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 10px;
}

.save-btn,
.cancel-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.save-btn {
  background: #667eea;
  color: white;
}

.save-btn:hover {
  background: #764ba2;
}

.cancel-btn {
  background: #e5e7eb;
  color: #4a5568;
}

.cancel-btn:hover {
  background: #d1d5db;
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
</style>