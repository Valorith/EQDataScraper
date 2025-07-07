<template>
  <div class="admin-system">
    <div class="page-header">
      <div class="header-content">
        <router-link to="/admin" class="back-link">
          <i class="fas fa-arrow-left"></i>
          Back to Dashboard
        </router-link>
        <h1>System Monitoring</h1>
        <p class="subtitle">Monitor application health and performance metrics</p>
      </div>
    </div>

    <!-- System Health Overview -->
    <div class="health-overview">
      <div class="health-card" :class="systemHealthClass">
        <div class="health-icon">
          <i :class="systemHealthIcon"></i>
        </div>
        <div class="health-content">
          <h2>System Health</h2>
          <div class="health-status">{{ systemHealthText }}</div>
          <div class="health-details">
            <div class="detail-item">
              <span class="label">Uptime:</span>
              <span class="value">{{ formatUptime(systemStats.uptime) || 'Calculating...' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Last Check:</span>
              <span class="value">{{ formatTime(lastCheck) || 'Just now' }}</span>
            </div>
          </div>
        </div>
        <div class="health-score">
          <div class="score-value">{{ healthScore }}%</div>
          <div class="score-label">Health Score</div>
        </div>
      </div>
    </div>

    <!-- Performance Metrics -->
    <div class="metrics-section">
      <h2>Performance Metrics</h2>
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-header">
            <i class="fas fa-tachometer-alt"></i>
            <h3>Response Time</h3>
          </div>
          <div class="metric-value">{{ systemStats.avgResponseTime || 0 }}ms</div>
          <div class="metric-chart">
            <div class="mini-chart" v-for="(value, index) in responseTimeHistory" :key="`chart-${index}`">
              <div 
                class="chart-bar" 
                :style="{ height: (value / maxResponseTime * 100) + '%' }"
              ></div>
            </div>
          </div>
          <div class="metric-info">
            <span :class="responseTimeClass">{{ responseTimeStatus }}</span>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-header">
            <i class="fas fa-server"></i>
            <h3>Server Load</h3>
          </div>
          <div class="metric-value">{{ Math.min(Math.round(systemStats.serverLoad || 0), 100) }}%</div>
          <div class="load-bar">
            <div class="load-fill" :style="{ width: Math.min(systemStats.serverLoad || 0, 100) + '%' }"></div>
          </div>
          <div class="metric-info">
            <span :class="serverLoadClass">{{ serverLoadStatus }}</span>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-header">
            <i class="fas fa-memory"></i>
            <h3>Memory Usage</h3>
          </div>
          <div class="metric-value">{{ formatBytes(systemStats.memoryUsed) }}</div>
          <div class="memory-info">
            <div class="memory-bar">
              <div 
                class="memory-fill" 
                :style="{ width: memoryPercentage + '%' }"
              ></div>
            </div>
            <div class="memory-text">
              {{ formatBytes(systemStats.memoryUsed) }} / {{ formatBytes(systemStats.memoryTotal) }}
            </div>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-header">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Error Rate</h3>
          </div>
          <div class="metric-value">{{ systemStats.errorRate || 0 }}%</div>
          <div class="error-info">
            <div class="error-count">{{ systemStats.errorCount || 0 }} errors</div>
            <div class="error-period">Last 24 hours</div>
          </div>
          <div class="metric-info">
            <span :class="errorRateClass">{{ errorRateStatus }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Database Metrics -->
    <div class="metrics-section" v-if="databaseStats">
      <h2>Database Performance</h2>
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-header">
            <i class="fas fa-database"></i>
            <h3>Total Queries</h3>
          </div>
          <div class="metric-value">{{ databaseStats.total_queries || 0 }}</div>
          <div class="metric-info">
            <span class="good">{{ formatNumber(databaseStats.total_queries) }} queries executed</span>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-header">
            <i class="fas fa-clock"></i>
            <h3>Avg Query Time</h3>
          </div>
          <div class="metric-value">{{ Math.round(databaseStats.avg_query_time || 0) }}ms</div>
          <div class="metric-info">
            <span :class="queryTimeClass">{{ queryTimeStatus }}</span>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-header">
            <i class="fas fa-exclamation-circle"></i>
            <h3>Slow Queries</h3>
          </div>
          <div class="metric-value">{{ databaseStats.slow_queries_count || 0 }}</div>
          <div class="metric-info">
            <span :class="slowQueryClass">{{ slowQueryStatus }}</span>
          </div>
        </div>

        <div class="metric-card query-breakdown">
          <div class="metric-header">
            <i class="fas fa-chart-pie"></i>
            <h3>Query Breakdown</h3>
          </div>
          <div class="query-types">
            <div v-for="(count, type) in databaseStats.query_types" :key="`query-type-${type}`" class="query-type">
              <span class="type-label">{{ type }}:</span>
              <span class="type-count">{{ count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Tables Accessed -->
      <div class="tables-section" v-if="databaseStats.tables_accessed && Object.keys(databaseStats.tables_accessed).length > 0">
        <h3>Most Accessed Tables</h3>
        <div class="tables-grid">
          <div v-for="(count, table) in sortedTables" :key="`table-${table}`" class="table-item">
            <span class="table-name">{{ table }}</span>
            <span class="table-count">{{ count }} queries</span>
          </div>
        </div>
      </div>

      <!-- Query Timeline Graph -->
      <div class="query-timeline-section">
        <div class="timeline-header">
          <h3>Query Activity Timeline</h3>
          <div class="time-scale-selector">
            <button 
              v-for="scale in timeScales" 
              :key="scale.value"
              @click="selectedTimeScale = scale.value"
              :class="['scale-btn', { active: selectedTimeScale === scale.value }]"
            >
              {{ scale.label }}
            </button>
          </div>
        </div>
        <div class="timeline-chart">
          <canvas ref="queryTimelineChart" width="800" height="300"></canvas>
        </div>
        <div class="timeline-legend">
          <div v-for="(color, table) in tableColors" :key="`legend-${table}`" class="legend-item">
            <span class="legend-color" :style="{ backgroundColor: color }"></span>
            <span class="legend-label">{{ table }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- API Endpoints Status -->
    <div class="endpoints-section">
      <h2>API Endpoints Status</h2>
      <div class="endpoints-grid">
        <div 
          v-for="(endpoint, idx) in apiEndpoints" 
          :key="`endpoint-${endpoint.method}-${endpoint.path}-${idx}`"
          class="endpoint-card"
          :class="endpoint.status"
        >
          <div class="endpoint-header">
            <div class="endpoint-method">{{ endpoint.method }}</div>
            <div class="endpoint-path">{{ endpoint.path }}</div>
          </div>
          <div class="endpoint-stats">
            <div class="stat">
              <span class="label">Avg Response:</span>
              <span class="value">{{ endpoint.avgTime }}ms</span>
            </div>
            <div class="stat">
              <span class="label">Calls/hour:</span>
              <span class="value">{{ endpoint.callsPerHour }}</span>
            </div>
            <div class="stat">
              <span class="label">Success Rate:</span>
              <span class="value">{{ endpoint.successRate }}%</span>
            </div>
          </div>
          <div class="endpoint-status">
            <i :class="getStatusIcon(endpoint.status)"></i>
            {{ endpoint.status }}
          </div>
        </div>
      </div>
    </div>

    <!-- System Logs -->
    <div class="logs-section">
      <div class="logs-header">
        <h2>System Logs</h2>
        <div class="logs-controls">
          <select v-model="logLevel" class="log-filter">
            <option value="all">All Levels</option>
            <option value="error">Errors</option>
            <option value="warning">Warnings</option>
            <option value="info">Info</option>
          </select>
          <button @click="refreshLogs" class="refresh-btn">
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': refreshingLogs }"></i>
            Refresh
          </button>
        </div>
      </div>
      <div class="logs-container">
        <div v-for="(log, logIndex) in filteredLogs" :key="`log-${log.id || logIndex}-${logIndex}`" class="log-entry" :class="log.level">
          <div class="log-time">{{ formatLogTime(log.timestamp) }}</div>
          <div class="log-level">{{ log.level.toUpperCase() }}</div>
          <div class="log-content">
            <div class="log-message">{{ log.message }}</div>
            <div v-if="log.context" class="log-context">{{ log.context }}</div>
          </div>
        </div>
        <div v-if="filteredLogs.length === 0" class="no-logs">
          No logs to display
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import { API_BASE_URL, buildApiUrl, API_ENDPOINTS } from '../config/api'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()

// State
const systemStats = ref({
  uptime: Date.now() - (24 * 60 * 60 * 1000), // Default to 24 hours ago
  avgResponseTime: 0,
  serverLoad: 0,
  memoryUsed: 0,
  memoryTotal: 8589934592, // 8GB default
  errorRate: 0,
  errorCount: 0
})

const healthScore = ref(100)
const lastCheck = ref(new Date())
const responseTimeHistory = ref(Array(20).fill(0))
const maxResponseTime = ref(1000)
const apiEndpoints = ref([])
const systemLogs = ref([])
const logLevel = ref('all')
const refreshingLogs = ref(false)
const databaseStats = ref(null)

let updateInterval = null

// Query timeline graph state
const queryTimelineChart = ref(null)
const selectedTimeScale = ref('1h')
const timeScales = [
  { value: '1h', label: '1 Hour' },
  { value: '6h', label: '6 Hours' },
  { value: '24h', label: '24 Hours' },
  { value: '7d', label: '7 Days' }
]
const tableColors = ref({})
const queryTimelineData = ref({})

// Computed
const systemHealthClass = computed(() => {
  if (healthScore.value >= 90) return 'healthy'
  if (healthScore.value >= 70) return 'warning'
  return 'critical'
})

const systemHealthText = computed(() => {
  if (healthScore.value >= 90) return 'All Systems Operational'
  if (healthScore.value >= 70) return 'Minor Issues Detected'
  return 'Critical Issues Present'
})

const systemHealthIcon = computed(() => {
  if (healthScore.value >= 90) return 'fas fa-check-circle'
  if (healthScore.value >= 70) return 'fas fa-exclamation-triangle'
  return 'fas fa-times-circle'
})

const responseTimeClass = computed(() => {
  const time = systemStats.value.avgResponseTime
  if (time <= 200) return 'good'
  if (time <= 500) return 'warning'
  return 'critical'
})

const responseTimeStatus = computed(() => {
  const time = systemStats.value.avgResponseTime
  if (time <= 200) return 'Excellent'
  if (time <= 500) return 'Acceptable'
  return 'Poor'
})

const serverLoadClass = computed(() => {
  const load = systemStats.value.serverLoad
  if (load <= 50) return 'good'
  if (load <= 80) return 'warning'
  return 'critical'
})

const serverLoadStatus = computed(() => {
  const load = systemStats.value.serverLoad
  if (load <= 50) return 'Normal'
  if (load <= 80) return 'High'
  return 'Overloaded'
})

const memoryPercentage = computed(() => {
  if (!systemStats.value.memoryTotal) return 0
  return (systemStats.value.memoryUsed / systemStats.value.memoryTotal) * 100
})

const errorRateClass = computed(() => {
  const rate = systemStats.value.errorRate
  if (rate <= 1) return 'good'
  if (rate <= 5) return 'warning'
  return 'critical'
})

const errorRateStatus = computed(() => {
  const rate = systemStats.value.errorRate
  if (rate <= 1) return 'Normal'
  if (rate <= 5) return 'Elevated'
  return 'Critical'
})

const filteredLogs = computed(() => {
  if (logLevel.value === 'all') return systemLogs.value
  return systemLogs.value.filter(log => log.level === logLevel.value)
})

const queryTimeClass = computed(() => {
  if (!databaseStats.value) return 'good'
  const time = databaseStats.value.avg_query_time
  if (time <= 50) return 'good'
  if (time <= 100) return 'warning'
  return 'critical'
})

const queryTimeStatus = computed(() => {
  if (!databaseStats.value) return 'Fast'
  const time = databaseStats.value.avg_query_time
  if (time <= 50) return 'Fast'
  if (time <= 100) return 'Moderate'
  return 'Slow'
})

const slowQueryClass = computed(() => {
  if (!databaseStats.value) return 'good'
  const count = databaseStats.value.slow_queries_count
  if (count === 0) return 'good'
  if (count <= 5) return 'warning'
  return 'critical'
})

const slowQueryStatus = computed(() => {
  if (!databaseStats.value) return 'None'
  const count = databaseStats.value.slow_queries_count
  if (count === 0) return 'None'
  if (count <= 5) return 'Few slow queries'
  return 'Many slow queries'
})

const sortedTables = computed(() => {
  if (!databaseStats.value || !databaseStats.value.tables_accessed) return {}
  // Sort tables by access count and take top 5
  return Object.entries(databaseStats.value.tables_accessed)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .reduce((obj, [key, val]) => {
      obj[key] = val
      return obj
    }, {})
})

// Methods
const loadSystemStats = async () => {
  try {
    // Check if user has proper authentication
    const isAdmin = userStore.user && userStore.user.role === 'admin'
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    
    if (!isAdmin) {
      console.log('Loading limited system metrics for non-admin user')
      // Load basic health data that doesn't require admin
      try {
        const healthResponse = await axios.get(`${API_BASE_URL}/api/health`)
        if (healthResponse.data) {
          systemStats.value = {
            uptime: 0,
            avgResponseTime: 0,
            serverLoad: 0,
            memoryUsed: 0,
            memoryTotal: 100,
            errorRate: 0,
            errorCount: 0
          }
          healthScore.value = healthResponse.data.status === 'healthy' ? 100 : 50
          loading.value = false
        }
      } catch (healthError) {
        console.log('Could not load health data')
        loading.value = false
      }
      return
    }

    // Load comprehensive system metrics for admins
    const headers = {
      'Authorization': `Bearer ${token}`
    }
    
    const metricsResponse = await axios.get(`${API_BASE_URL}/api/admin/system/metrics`, { headers })
    const metricsData = metricsResponse.data.data
    
    // Update system stats with real data
    systemStats.value = {
      uptime: metricsData.system.uptime_seconds,
      avgResponseTime: metricsData.performance.avg_response_time,
      serverLoad: metricsData.system.cpu_percent,
      memoryUsed: metricsData.system.memory.used,
      memoryTotal: metricsData.system.memory.total,
      errorRate: metricsData.performance.error_rate,
      errorCount: metricsData.performance.error_count
    }
    
    // Use the calculated health score from backend
    healthScore.value = metricsData.health_score
    
    // Update database stats
    databaseStats.value = metricsData.database
    
    // Generate table colors if we have table data
    if (databaseStats.value?.tables_accessed) {
      tableColors.value = generateTableColors(databaseStats.value.tables_accessed)
      // Draw the timeline chart
      setTimeout(() => drawQueryTimeline(), 100)
    }
    
    // Update response time history
    if (metricsData.performance.response_time_history && metricsData.performance.response_time_history.length > 0) {
      responseTimeHistory.value = metricsData.performance.response_time_history
      // Pad with zeros if less than 20 values
      while (responseTimeHistory.value.length < 20) {
        responseTimeHistory.value.unshift(0)
      }
    }
    
    // Update last check
    lastCheck.value = new Date()
    
    // Load API endpoints status
    await loadEndpointsStatus()
    
  } catch (error) {
    if (error.response?.status === 401) {
      console.log('System metrics require authentication')
      // Don't redirect, just show limited data
      systemStats.value = {
        uptime: 0,
        avgResponseTime: 0,
        serverLoad: 0,
        memoryUsed: 0,
        memoryTotal: 100,
        errorRate: 0,
        errorCount: 0
      }
      healthScore.value = 50
    } else if (error.response?.status === 403) {
      console.log('System metrics require admin privileges')
      // Don't redirect, just show limited data
      systemStats.value = {
        uptime: 0,
        avgResponseTime: 0,
        serverLoad: 0,
        memoryUsed: 0,
        memoryTotal: 100,
        errorRate: 0,
        errorCount: 0
      }
      healthScore.value = 50
      router.push('/admin')
    } else if (error.response?.status === 404) {
      console.log('System metrics endpoint not found')
    } else if (error.response) {
      console.warn('Error loading system stats:', error.response.status)
    } else {
      console.warn('Could not reach system metrics endpoint')
    }
  }
}

const loadEndpointsStatus = async () => {
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const headers = {
      'Authorization': `Bearer ${token}`
    }
    
    const endpointsResponse = await axios.get(`${API_BASE_URL}/api/admin/system/endpoints`, { headers })
    apiEndpoints.value = endpointsResponse.data.data.endpoints
    
    // Load logs after endpoints
    await loadSystemLogs()
  } catch (error) {
    if (error.response?.status !== 404) {
      console.warn('Could not load endpoint metrics')
    }
    // Fall back to some default endpoints if error
    apiEndpoints.value = [
      {
        method: 'GET',
        path: '/api/classes',
        avgTime: 0,
        callsPerHour: 0,
        successRate: 100.0,
        status: 'healthy'
      }
    ]
  }
}

// Removed unused generateSampleLogs function - component now uses real logs from API

const refreshLogs = async () => {
  refreshingLogs.value = true
  try {
    await loadSystemLogs()
  } finally {
    setTimeout(() => {
      refreshingLogs.value = false
    }, 500)
  }
}

const loadSystemLogs = async () => {
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const headers = {
      'Authorization': `Bearer ${token}`
    }
    
    const params = {
      level: logLevel.value,
      limit: 50
    }
    
    const logsResponse = await axios.get(`${API_BASE_URL}/api/admin/system/logs`, { headers, params })
    systemLogs.value = logsResponse.data.data.logs
  } catch (error) {
    // Silently keep existing logs if error
    if (error.response?.status !== 404 && error.response?.status !== 401) {
      console.log('Using cached logs')
    }
  }
}

const formatUptime = (startTime) => {
  if (!startTime) return '0m'
  const diff = Date.now() - startTime
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  
  if (days > 0) return `${days}d ${hours}h`
  if (hours > 0) return `${hours}h ${minutes}m`
  return `${minutes}m`
}

const formatTime = (date) => {
  return new Date(date).toLocaleTimeString()
}

const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatLogTime = (timestamp) => {
  return new Date(timestamp).toLocaleString()
}

const getStatusIcon = (status) => {
  const icons = {
    healthy: 'fas fa-check-circle',
    warning: 'fas fa-exclamation-triangle',
    critical: 'fas fa-times-circle'
  }
  return icons[status] || 'fas fa-info-circle'
}

const formatNumber = (num) => {
  if (!num) return '0'
  return num.toLocaleString()
}

// Generate colors for tables
const generateTableColors = (tables) => {
  const colors = [
    '#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe',
    '#fa709a', '#fee140', '#30cfd0', '#330867', '#a8edea'
  ]
  const colorMap = {}
  Object.keys(tables).forEach((table, index) => {
    colorMap[table] = colors[index % colors.length]
  })
  return colorMap
}

// Draw query timeline chart
const drawQueryTimeline = () => {
  if (!queryTimelineChart.value) return
  
  const canvas = queryTimelineChart.value
  const ctx = canvas.getContext('2d')
  const width = canvas.width
  const height = canvas.height
  
  // Clear canvas
  ctx.clearRect(0, 0, width, height)
  
  // Set up chart area
  const padding = 40
  const chartWidth = width - 2 * padding
  const chartHeight = height - 2 * padding
  
  // Draw background
  ctx.fillStyle = 'rgba(30, 30, 50, 0.3)'
  ctx.fillRect(padding, padding, chartWidth, chartHeight)
  
  // Get data based on selected time scale
  const timelineData = generateTimelineData()
  if (!timelineData || timelineData.length === 0) return
  
  // Find max value for scaling
  const maxValue = Math.max(...timelineData.flatMap(point => 
    Object.values(point.data).reduce((sum, val) => sum + val, 0)
  )) || 1
  
  // Draw grid lines
  ctx.strokeStyle = 'rgba(156, 163, 175, 0.1)'
  ctx.lineWidth = 1
  
  // Horizontal grid lines
  for (let i = 0; i <= 5; i++) {
    const y = padding + (chartHeight * i) / 5
    ctx.beginPath()
    ctx.moveTo(padding, y)
    ctx.lineTo(padding + chartWidth, y)
    ctx.stroke()
    
    // Y-axis labels
    ctx.fillStyle = '#9ca3af'
    ctx.font = '12px sans-serif'
    ctx.textAlign = 'right'
    const value = Math.round(maxValue * (5 - i) / 5)
    ctx.fillText(value.toString(), padding - 10, y + 4)
  }
  
  // Draw lines for each table
  Object.entries(tableColors.value).forEach(([table, color]) => {
    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.beginPath()
    
    timelineData.forEach((point, index) => {
      const x = padding + (index / (timelineData.length - 1)) * chartWidth
      const y = padding + chartHeight - (point.data[table] || 0) / maxValue * chartHeight
      
      if (index === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    })
    
    ctx.stroke()
  })
  
  // Draw X-axis labels
  ctx.fillStyle = '#9ca3af'
  ctx.font = '11px sans-serif'
  ctx.textAlign = 'center'
  
  const labelInterval = Math.ceil(timelineData.length / 6)
  timelineData.forEach((point, index) => {
    if (index % labelInterval === 0 || index === timelineData.length - 1) {
      const x = padding + (index / (timelineData.length - 1)) * chartWidth
      ctx.fillText(point.time, x, height - 10)
    }
  })
}

// Generate timeline data based on selected scale
const generateTimelineData = () => {
  // Use real timeline data from backend if available
  const timeline = databaseStats.value?.timeline || []
  if (timeline.length === 0) {
    return []
  }
  
  const now = new Date()
  const points = []
  
  // Determine how many hours to include based on time scale
  let hoursToInclude = 1
  if (selectedTimeScale.value === '1h') hoursToInclude = 1
  else if (selectedTimeScale.value === '6h') hoursToInclude = 6
  else if (selectedTimeScale.value === '24h') hoursToInclude = 24
  else if (selectedTimeScale.value === '7d') hoursToInclude = 168
  
  // Get the relevant timeline entries
  const relevantEntries = timeline.slice(-hoursToInclude)
  
  // Aggregate data based on time scale
  if (selectedTimeScale.value === '1h') {
    // For 1 hour, show data points every 5 minutes (interpolated)
    for (let i = 0; i < 12; i++) {
      const entry = relevantEntries[0] || { tables: {} }
      const data = {}
      Object.keys(entry.tables || {}).forEach(table => {
        // Distribute the hourly count across 5-minute intervals
        data[table] = Math.round((entry.tables[table] || 0) / 12)
      })
      points.push({ 
        time: `-${(11 - i) * 5}m`, 
        data 
      })
    }
  } else if (selectedTimeScale.value === '6h' || selectedTimeScale.value === '24h') {
    // Show hourly data
    relevantEntries.forEach((entry, index) => {
      const hoursAgo = relevantEntries.length - index - 1
      points.push({
        time: `-${hoursAgo}h`,
        data: entry.tables || {}
      })
    })
  } else if (selectedTimeScale.value === '7d') {
    // Aggregate by day
    const dailyData = {}
    relevantEntries.forEach(entry => {
      const date = new Date(entry.timestamp)
      const dayKey = date.toISOString().split('T')[0]
      
      if (!dailyData[dayKey]) {
        dailyData[dayKey] = {}
      }
      
      Object.entries(entry.tables || {}).forEach(([table, count]) => {
        dailyData[dayKey][table] = (dailyData[dayKey][table] || 0) + count
      })
    })
    
    // Convert to points
    const days = Object.keys(dailyData).sort()
    days.forEach((day, index) => {
      const daysAgo = days.length - index - 1
      points.push({
        time: `-${daysAgo}d`,
        data: dailyData[day]
      })
    })
  }
  
  // Ensure we have data for all accessed tables
  const allTables = Object.keys(databaseStats.value?.tables_accessed || {})
  points.forEach(point => {
    allTables.forEach(table => {
      if (!(table in point.data)) {
        point.data[table] = 0
      }
    })
  })
  
  return points
}

// Watch for time scale changes
watch(selectedTimeScale, () => {
  drawQueryTimeline()
})

// Lifecycle
onMounted(() => {
  // Check authentication first
  if (!userStore.isAuthenticated || userStore.user?.role !== 'admin') {
    router.push('/admin')
    return
  }
  
  loadSystemStats()
  // Update stats every 5 seconds
  updateInterval = setInterval(loadSystemStats, 5000)
})

onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval)
  }
})
</script>

<style scoped>
.admin-system {
  padding: 20px;
  padding-top: 100px; /* Increased padding to prevent logo overlap */
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1e 100%);
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
  text-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
}

.subtitle {
  color: #9ca3af;
  font-size: 1.1rem;
  margin: 0;
  opacity: 0.9;
}

.health-overview {
  margin-bottom: 40px;
}

.health-card {
  background: rgba(30, 30, 50, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 15px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  padding: 30px;
  display: flex;
  align-items: center;
  gap: 30px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  transition: all 0.3s;
}

.health-card.healthy {
  border-color: #10b981;
}

.health-card.warning {
  border-color: #f59e0b;
}

.health-card.critical {
  border-color: #ef4444;
}

.health-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
}

.health-card.healthy .health-icon {
  background: #d1fae5;
  color: #10b981;
}

.health-card.warning .health-icon {
  background: #fef3c7;
  color: #f59e0b;
}

.health-card.critical .health-icon {
  background: #fee2e2;
  color: #ef4444;
}

.health-content {
  flex: 1;
}

.health-content h2 {
  margin: 0 0 10px 0;
  font-size: 1.5rem;
  color: #f3f4f6;
  font-weight: 600;
}

.health-status {
  font-size: 1.2rem;
  font-weight: 500;
  margin-bottom: 15px;
}

.health-details {
  display: flex;
  gap: 30px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.detail-item .label {
  color: #9ca3af;
  font-size: 0.9rem;
}

.detail-item .value {
  font-weight: 600;
  color: #e5e7eb;
}

.health-score {
  text-align: center;
  padding: 20px;
  background: rgba(102, 126, 234, 0.15);
  border-radius: 12px;
  border: 1px solid rgba(102, 126, 234, 0.3);
}

.score-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: #667eea;
}

.score-label {
  color: #9ca3af;
  font-size: 0.9rem;
}

.metrics-section {
  margin-bottom: 40px;
}

.metrics-section h2 {
  margin-bottom: 20px;
  color: #f3f4f6;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.metric-card {
  background: rgba(30, 30, 50, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  padding: 25px;
  border: 1px solid rgba(102, 126, 234, 0.1);
  transition: all 0.3s;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.3);
  border-color: rgba(102, 126, 234, 0.3);
}

.metric-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.metric-header i {
  font-size: 1.2rem;
  color: #667eea;
}

.metric-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #e5e7eb;
  font-weight: 600;
}

.metric-value {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 15px;
  color: #f3f4f6;
}

.metric-chart {
  display: flex;
  gap: 2px;
  height: 50px;
  align-items: flex-end;
  margin-bottom: 10px;
}

.chart-bar {
  flex: 1;
  background: #667eea;
  opacity: 0.6;
  transition: height 0.3s;
}

.mini-chart:last-child .chart-bar {
  opacity: 1;
}

.load-bar,
.memory-bar {
  width: 100%;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.load-fill,
.memory-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s;
}

.memory-text {
  font-size: 0.85rem;
  color: #9ca3af;
}

.error-info {
  margin-bottom: 10px;
}

.error-count {
  font-weight: 600;
}

.error-period {
  font-size: 0.85rem;
  color: #9ca3af;
}

.metric-info {
  font-weight: 500;
  font-size: 0.9rem;
  margin-top: 10px;
}

.metric-info .good {
  color: #10b981;
}

.metric-info .warning {
  color: #f59e0b;
}

.metric-info .critical {
  color: #ef4444;
}

.endpoints-section {
  margin-bottom: 40px;
}

.endpoints-section h2 {
  margin-bottom: 20px;
  color: #f3f4f6;
}

.endpoints-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 15px;
}

.endpoint-card {
  background: rgba(30, 30, 50, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 10px;
  padding: 20px;
  border: 2px solid rgba(102, 126, 234, 0.1);
  transition: all 0.3s;
}

.endpoint-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

.endpoint-card.healthy {
  border-color: #10b981;
}

.endpoint-card.warning {
  border-color: #f59e0b;
}

.endpoint-card.critical {
  border-color: #ef4444;
}

.endpoint-header {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.endpoint-method {
  background: #667eea;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 600;
}

.endpoint-path {
  font-weight: 500;
  color: #e5e7eb;
}

.endpoint-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 15px;
}

.endpoint-stats .stat {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.endpoint-stats .label {
  font-size: 0.75rem;
  color: #9ca3af;
}

.endpoint-stats .value {
  font-weight: 600;
  font-size: 0.9rem;
  color: #f3f4f6;
}

.endpoint-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  text-transform: capitalize;
}

.endpoint-card.healthy .endpoint-status {
  color: #10b981;
}

.endpoint-card.warning .endpoint-status {
  color: #f59e0b;
}

.endpoint-card.critical .endpoint-status {
  color: #ef4444;
}

.logs-section {
  background: rgba(30, 30, 50, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  padding: 25px;
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.logs-header h2 {
  margin: 0;
  color: #f3f4f6;
}

.logs-controls {
  display: flex;
  gap: 10px;
}

.log-filter {
  padding: 8px 12px;
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 6px;
  font-size: 0.9rem;
  background: rgba(30, 30, 50, 0.8);
  color: #e5e7eb;
}

.log-filter:focus {
  outline: none;
  border-color: rgba(102, 126, 234, 0.6);
}

.refresh-btn {
  padding: 8px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.2s;
}

.refresh-btn:hover {
  background: #764ba2;
}

.logs-container {
  max-height: 400px;
  overflow-y: auto;
  background: rgba(15, 15, 30, 0.5);
  border-radius: 8px;
  padding: 10px;
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.log-entry {
  display: grid;
  grid-template-columns: 150px 80px 1fr;
  gap: 15px;
  padding: 12px;
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.85rem;
  transition: background 0.2s;
  border-radius: 4px;
}

.log-entry:hover {
  background: rgba(102, 126, 234, 0.1);
}

.log-entry:last-child {
  border-bottom: none;
}

.log-time {
  color: #9ca3af;
}

.log-level {
  font-weight: 600;
  text-transform: uppercase;
}

.log-entry.error {
  background: rgba(239, 68, 68, 0.1);
}

.log-entry.error:hover {
  background: rgba(239, 68, 68, 0.2);
}

.log-entry.error .log-level {
  color: #ef4444;
}

.log-entry.warning {
  background: rgba(245, 158, 11, 0.1);
}

.log-entry.warning:hover {
  background: rgba(245, 158, 11, 0.2);
}

.log-entry.warning .log-level {
  color: #f59e0b;
}

.log-entry.info .log-level {
  color: #3b82f6;
}

.log-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.log-message {
  color: #e5e7eb;
  font-weight: 500;
}

.log-context {
  color: #9ca3af;
  font-size: 0.8rem;
  line-height: 1.4;
}

.no-logs {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
}

/* Database metrics styles */
.query-breakdown {
  grid-column: span 2;
}

.query-types {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
  margin-top: 10px;
}

.query-type {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.type-label {
  font-size: 0.85rem;
  color: #9ca3af;
  margin-bottom: 5px;
}

.type-count {
  font-size: 1.2rem;
  font-weight: 600;
  color: #667eea;
}

.tables-section {
  margin-top: 20px;
}

.tables-section h3 {
  color: #e5e7eb;
  margin-bottom: 15px;
  font-size: 1.2rem;
}

.tables-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
}

.table-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(30, 30, 50, 0.4);
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.1);
  transition: all 0.2s;
}

.table-item:hover {
  background: rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.3);
}

.table-name {
  font-weight: 500;
  color: #e5e7eb;
  text-transform: lowercase;
}

.table-count {
  color: #667eea;
  font-weight: 600;
  font-size: 0.9rem;
}

/* Scrollbar styling for dark theme */
.logs-container::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.logs-container::-webkit-scrollbar-track {
  background: rgba(30, 30, 50, 0.3);
  border-radius: 4px;
}

.logs-container::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.4);
  border-radius: 4px;
}

.logs-container::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.6);
}

/* Refresh button dark theme */
.refresh-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
  box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
}

.refresh-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

/* Query Timeline Styles */
.query-timeline-section {
  margin-top: 30px;
  padding: 25px;
  background: rgba(30, 30, 50, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.timeline-header h3 {
  margin: 0;
  color: #e5e7eb;
  font-size: 1.2rem;
  font-weight: 600;
}

.time-scale-selector {
  display: flex;
  gap: 8px;
}

.scale-btn {
  padding: 6px 14px;
  background: rgba(30, 30, 50, 0.8);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 6px;
  color: #9ca3af;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.scale-btn:hover {
  background: rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.4);
  color: #e5e7eb;
}

.scale-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  color: white;
  box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
}

.timeline-chart {
  background: rgba(15, 15, 30, 0.5);
  border-radius: 8px;
  padding: 10px;
  border: 1px solid rgba(102, 126, 234, 0.1);
  overflow-x: auto;
}

.timeline-chart canvas {
  display: block;
  margin: 0 auto;
}

.timeline-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(102, 126, 234, 0.1);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.legend-label {
  color: #e5e7eb;
  font-size: 0.85rem;
  font-weight: 500;
  text-transform: lowercase;
}

@media (max-width: 768px) {
  .health-card {
    flex-direction: column;
    text-align: center;
  }

  .health-details {
    flex-direction: column;
    gap: 10px;
  }

  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .endpoints-grid {
    grid-template-columns: 1fr;
  }

  .log-entry {
    grid-template-columns: 1fr;
    gap: 5px;
  }
  
  .query-breakdown {
    grid-column: span 1;
  }
}
</style>