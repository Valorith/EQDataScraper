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
            <div class="detail-item">
              <span class="label">Backend Status:</span>
              <span class="value heartbeat-status" :class="heartbeatClass">
                <i class="fas fa-circle heartbeat-dot" :class="heartbeatClass"></i>
                {{ heartbeatStatus }}
              </span>
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
      <div class="section-header">
        <h2>Database Performance</h2>
        <button 
          class="reset-button"
          @click="showResetConfirmation = true"
          :disabled="isResetting"
          title="Reset all database performance metrics and tracking data"
        >
          <i class="fas fa-undo"></i>
          Reset Metrics
        </button>
      </div>
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
          <div v-for="(count, table) in sortedTables" :key="`table-${table}`" class="table-item clickable" @click="showTableBreakdown(table)">
            <div class="table-info">
              <span class="table-name">{{ table }}</span>
              <span class="table-count">{{ count }} queries</span>
            </div>
            <span class="table-arrow">→</span>
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
        <div class="timeline-legends">
          <div class="timeline-legend">
            <h4 class="legend-title">Tables</h4>
            <div class="legend-items">
              <div v-for="(color, table) in tableColors" :key="`legend-${table}`" class="legend-item">
                <span class="legend-color" :style="{ backgroundColor: color }"></span>
                <span class="legend-label">{{ table }}</span>
              </div>
            </div>
          </div>
          
          <div class="timeline-legend">
            <h4 class="legend-title">Query Load Thresholds</h4>
            <div class="legend-items">
              <div class="legend-item">
                <span class="legend-ring threshold-normal"></span>
                <span class="legend-label">Normal</span>
              </div>
              <div class="legend-item">
                <span class="legend-ring threshold-moderate"></span>
                <span class="legend-label">Moderate</span>
              </div>
              <div class="legend-item">
                <span class="legend-ring threshold-high"></span>
                <span class="legend-label">High</span>
              </div>
              <div class="legend-item">
                <span class="legend-ring threshold-critical"></span>
                <span class="legend-label">Critical</span>
              </div>
            </div>
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
        <!-- Table Headers -->
        <div class="logs-header-row">
          <div class="header-time">Timestamp</div>
          <div class="header-level">Level</div>
          <div class="header-message">Message & Details</div>
        </div>
        
        <div v-for="(log, logIndex) in filteredLogs" :key="`log-${log.id || logIndex}-${logIndex}`" class="log-entry" :class="[log.level, { 'endpoint-failure': isEndpointFailure(log), 'expandable': hasExpandableDetails(log) }]" @click="toggleLogDetails(log)">
          <div class="log-time">{{ formatLogTime(log.timestamp) }}</div>
          <div class="log-level">{{ log.level.toUpperCase() }}</div>
          <div class="log-content">
            <div class="log-message">
              <span class="message-text">{{ log.message }}</span>
              <span v-if="isEndpointFailure(log)" class="endpoint-failure-badge">Endpoint Failure</span>
              <span v-if="hasExpandableDetails(log)" class="expand-icon" :class="{ 'expanded': log.expanded }">
                <i class="fas fa-chevron-down"></i>
              </span>
            </div>
            <div v-if="log.context" class="log-context">{{ log.context }}</div>
            <div v-if="log.expanded" class="log-details">
              <!-- Log Overview -->
              <div class="detail-section">
                <h4 class="section-title">
                  <span class="section-icon">{{ getLogTypeInfo(log).icon }}</span>
                  Log Details
                </h4>
                <div class="detail-grid">
                  <div class="detail-item">
                    <span class="detail-label">Type:</span>
                    <span class="detail-value">{{ getLogTypeInfo(log).category }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">Severity:</span>
                    <span class="detail-value" :class="getLogSeverity(log).color">{{ getLogSeverity(log).level }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">Full Timestamp:</span>
                    <span class="detail-value timestamp">{{ new Date(log.timestamp).toLocaleString() || 'Unknown' }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">Log ID:</span>
                    <span class="detail-value">{{ log.id || 'N/A' }}</span>
                  </div>
                </div>
                <div class="detail-item full-width">
                  <span class="detail-label">Description:</span>
                  <span class="detail-value">{{ getLogTypeInfo(log).description }}</span>
                </div>
              </div>
              
              <!-- Message Details -->
              <div class="detail-section">
                <h4 class="section-title">
                  <span class="section-icon">💬</span>
                  Message Information
                </h4>
                <div class="detail-item full-width">
                  <span class="detail-label">Full Message:</span>
                  <div class="detail-value message-content">{{ log.message }}</div>
                </div>
                <div v-if="log.context" class="detail-item full-width">
                  <span class="detail-label">Context:</span>
                  <span class="detail-value context-badge">{{ log.context }}</span>
                </div>
              </div>
              
              <!-- Technical Details (if available) -->
              <div v-if="log.endpoint || log.statusCode || log.responseTime || log.errorDetails || log.stackTrace" class="detail-section">
                <h4 class="section-title">
                  <span class="section-icon">⚙️</span>
                  Technical Information
                </h4>
                <div class="detail-grid">
                  <div v-if="log.endpoint" class="detail-item">
                    <span class="detail-label">Endpoint:</span>
                    <span class="detail-value endpoint-badge">{{ log.endpoint }}</span>
                  </div>
                  <div v-if="log.statusCode" class="detail-item">
                    <span class="detail-label">Status Code:</span>
                    <span class="detail-value status-code" :class="getStatusCodeClass(log.statusCode)">{{ log.statusCode }}</span>
                  </div>
                  <div v-if="log.responseTime" class="detail-item">
                    <span class="detail-label">Response Time:</span>
                    <span class="detail-value">{{ log.responseTime }}ms</span>
                  </div>
                </div>
                <div v-if="log.errorDetails" class="detail-item full-width">
                  <span class="detail-label">Error Details:</span>
                  <pre class="detail-value error-details">{{ log.errorDetails }}</pre>
                </div>
                <div v-if="log.stackTrace" class="detail-item full-width">
                  <span class="detail-label">Stack Trace:</span>
                  <pre class="detail-value stack-trace">{{ log.stackTrace }}</pre>
                </div>
              </div>
              
              <!-- Actions -->
              <div class="detail-actions">
                <button @click.stop="copyLogDetails(log)" class="action-btn copy-btn">
                  <i class="fas fa-copy"></i>
                  Copy Details
                </button>
                <button v-if="log.level === 'error'" @click.stop="reportIssue(log)" class="action-btn report-btn">
                  <i class="fas fa-bug"></i>
                  Report Issue
                </button>
              </div>
            </div>
          </div>
        </div>
        <div v-if="filteredLogs.length === 0" class="no-logs">
          No logs to display
        </div>
      </div>
    </div>

    <!-- Table Breakdown Modal -->
    <div v-if="showTableModal" class="modal-overlay" @click="closeTableModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Query Sources for "{{ selectedTable }}"</h3>
          <button class="close-btn" @click="closeTableModal">×</button>
        </div>
        <div class="modal-body">
          <div v-if="tableBreakdownLoading" class="loading">
            <div class="spinner"></div>
            <p>Loading breakdown...</p>
          </div>
          <div v-else-if="tableBreakdown.sources && tableBreakdown.sources.length > 0" class="breakdown-list">
            <div class="breakdown-summary">
              <p><strong>Total Queries:</strong> {{ tableBreakdown.total_queries }}</p>
            </div>
            <div v-for="(source, index) in tableBreakdown.sources" :key="`source-${index}`" class="source-item">
              <div class="source-header">
                <span class="source-endpoint">{{ source.endpoint }}</span>
                <span class="source-count">{{ source.query_count }} queries ({{ source.percentage }}%)</span>
              </div>
              <div class="source-bar">
                <div class="source-fill" :style="{ width: source.percentage + '%' }"></div>
              </div>
            </div>
          </div>
          <div v-else-if="tableBreakdown.error" class="error-state">
            <p><strong>Error:</strong> {{ tableBreakdown.error }}</p>
          </div>
          <div v-else class="no-data">
            <p>No source data available for this table.</p>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Reset Confirmation Modal -->
  <div v-if="showResetConfirmation" class="modal-overlay" @click="showResetConfirmation = false">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3><i class="fas fa-exclamation-triangle"></i> Reset Database Metrics</h3>
        <button class="close-button" @click="showResetConfirmation = false">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="modal-body">
        <p>Are you sure you want to reset all database performance metrics and tracking data?</p>
        <p class="warning-text">
          <i class="fas fa-info-circle"></i>
          This will permanently clear:
        </p>
        <ul class="reset-list">
          <li>Query execution times and history</li>
          <li>Slow query records</li>
          <li>Table access statistics</li>
          <li>Query type counters</li>
          <li>Timeline data</li>
        </ul>
        <p class="warning-text">This action cannot be undone.</p>
      </div>
      <div class="modal-footer">
        <button 
          class="cancel-button"
          @click="showResetConfirmation = false"
          :disabled="isResetting"
        >
          Cancel
        </button>
        <button 
          class="confirm-button"
          @click="resetDatabaseMetrics"
          :disabled="isResetting"
        >
          <i class="fas fa-undo"></i>
          {{ isResetting ? 'Resetting...' : 'Reset Metrics' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import { getApiBaseUrl, buildApiUrl, API_ENDPOINTS } from '../config/api'
import axios from 'axios'
import { requestManager } from '../utils/requestManager'

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
const loading = ref(false)

// Heartbeat monitoring
const heartbeatStatus = ref('Unknown')
const lastHeartbeat = ref(null)
const heartbeatFailures = ref(0)
let heartbeatInterval = null

let updateInterval = null

// Query timeline graph state
const queryTimelineChart = ref(null)
const selectedTimeScale = ref('6h')
const timeScales = [
  { value: '1h', label: '1 Hour' },
  { value: '6h', label: '6 Hours' },
  { value: '24h', label: '24 Hours' },
  { value: '7d', label: '7 Days' }
]
const tableColors = ref({})
const queryTimelineData = ref({})

// Table breakdown modal data
const showTableModal = ref(false)
const selectedTable = ref('')
const tableBreakdown = ref({})
const tableBreakdownLoading = ref(false)

// Reset confirmation modal data
const showResetConfirmation = ref(false)
const isResetting = ref(false)

// Computed
const systemHealthClass = computed(() => {
  if (healthScore.value >= 90) return 'healthy'
  if (healthScore.value >= 70) return 'warning'
  return 'critical'
})

// Heartbeat computed properties
const heartbeatClass = computed(() => {
  if (heartbeatStatus.value === 'Online') return 'good'
  if (heartbeatStatus.value === 'Degraded') return 'warning'
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
const checkHeartbeat = async () => {
  try {
    const startTime = Date.now()
    const response = await requestManager.get(`${getApiBaseUrl()}/api/health`, {
      timeout: 3000
    }, 'heartbeat')
    
    // Check if request was cancelled
    if (!response) {
      console.log('Heartbeat request was cancelled')
      return
    }
    
    const responseTime = Date.now() - startTime
    
    if (response.status === 200) {
      lastHeartbeat.value = new Date()
      heartbeatFailures.value = 0
      
      if (responseTime < 1000) {
        heartbeatStatus.value = 'Online'
        console.log(`🫀 Heartbeat: Online (${responseTime}ms)`)
      } else {
        heartbeatStatus.value = 'Degraded'
        console.log(`🫀 Heartbeat: Degraded (${responseTime}ms)`)
      }
    } else {
      throw new Error(`Backend returned status ${response.status}`)
    }
  } catch (error) {
    heartbeatFailures.value++
    
    if (heartbeatFailures.value >= 3) {
      heartbeatStatus.value = 'Offline'
    } else {
      heartbeatStatus.value = 'Degraded'
    }
    
    if (import.meta.env.MODE === 'development') {
      console.debug('Heartbeat check failed:', error.message)
    }
  }
}

const loadSystemStats = async () => {
  loading.value = true
  
  try {
    // Check if user has proper authentication or if OAuth is disabled
    const isAdmin = userStore.user && userStore.user.role === 'admin'
    const isOAuthDisabled = import.meta.env.MODE === 'development' && !userStore.user
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    
    // In dev mode with OAuth disabled, allow access to system metrics
    if (!isAdmin && !isOAuthDisabled) {
      console.log('Loading limited system metrics for non-admin user')
      // Load basic health data that doesn't require admin
      try {
        const healthResponse = await requestManager.get(`${getApiBaseUrl()}/api/health`, {
          timeout: 3000
        }, 'health-check')
        if (healthResponse && healthResponse.data) {
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
    
    console.log('Loading system metrics:', {
      isAdmin,
      isOAuthDisabled,
      hasToken: !!token,
      mode: import.meta.env.MODE
    })

    // Load comprehensive system metrics for admins
    const headers = {}
    // Only add auth header if we have a token and OAuth is enabled
    if (token && !isOAuthDisabled) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    const metricsResponse = await requestManager.get(`${getApiBaseUrl()}/api/admin/system/metrics`, { 
      headers,
      timeout: 15000 // 15 second timeout for admin metrics to match other endpoints
    }, 'system-metrics')
    
    // Check if request was cancelled
    if (!metricsResponse) {
      console.log('Metrics request was cancelled')
      return
    }
    
    console.log('Metrics response received:', {
      status: metricsResponse.status,
      data: metricsResponse.data,
      hasData: !!metricsResponse.data,
      hasNestedData: !!(metricsResponse.data && metricsResponse.data.data)
    })
    
    // Check if response contains expected data structure
    if (!metricsResponse.data || !metricsResponse.data.data) {
      console.error('Invalid metrics response structure. Expected response.data.data but got:', {
        responseData: metricsResponse.data,
        responseKeys: metricsResponse.data ? Object.keys(metricsResponse.data) : 'No data'
      })
      throw new Error('Invalid metrics response structure')
    }
    
    const metricsData = metricsResponse.data.data
    console.log('Metrics data extracted:', {
      hasSystem: !!metricsData.system,
      hasPerformance: !!metricsData.performance,
      systemKeys: metricsData.system ? Object.keys(metricsData.system) : 'No system data',
      performanceKeys: metricsData.performance ? Object.keys(metricsData.performance) : 'No performance data'
    })
    
    // Validate required fields exist
    if (!metricsData.system || !metricsData.performance) {
      console.error('Missing required metrics fields:', metricsData)
      throw new Error('Missing required metrics fields')
    }
    
    // Update system stats with real data (with fallbacks)
    systemStats.value = {
      uptime: metricsData.system?.uptime_seconds || 0,
      avgResponseTime: metricsData.performance?.avg_response_time || 0,
      serverLoad: metricsData.system?.cpu_percent || 0,
      memoryUsed: metricsData.system?.memory?.used || 0,
      memoryTotal: metricsData.system?.memory?.total || 100,
      errorRate: metricsData.performance?.error_rate || 0,
      errorCount: metricsData.performance?.error_count || 0
    }
    
    console.log('System stats updated:', systemStats.value)
    
    // Use the calculated health score from backend
    healthScore.value = metricsData.health_score
    
    // Update database stats
    databaseStats.value = metricsData.database
    
    // Generate table colors if we have table data
    if (databaseStats.value?.tables_accessed) {
      tableColors.value = generateTableColors(databaseStats.value.tables_accessed)
      // Draw the timeline chart
      setTimeout(() => {
        drawQueryTimeline()
      }, 100)
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
    
    // Set loading to false on success
    loading.value = false
    
  } catch (error) {
    console.error('Error loading system metrics:', error)
    
    // Set default stats for all error cases
    const defaultStats = {
      uptime: 0,
      avgResponseTime: 0,
      serverLoad: 0,
      memoryUsed: 0,
      memoryTotal: 100,
      errorRate: 0,
      errorCount: 0
    }
    
    if (error.response?.status === 401) {
      console.log('System metrics require authentication')
      systemStats.value = defaultStats
      healthScore.value = 50
    } else if (error.response?.status === 403) {
      console.log('System metrics require admin privileges')
      systemStats.value = defaultStats
      healthScore.value = 50
      router.push('/admin')
    } else if (error.response?.status === 404) {
      console.log('System metrics endpoint not found - ensure backend is running and endpoints are registered')
      systemStats.value = defaultStats
      healthScore.value = 0
    } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      console.log('System metrics request timed out - using fallback data')
      systemStats.value = defaultStats
      healthScore.value = 25 // Lower score for timeout
    } else if (error.message?.includes('Invalid metrics response')) {
      console.error('Invalid API response format - backend may be returning incorrect data structure')
      systemStats.value = defaultStats
      healthScore.value = 0
    } else if (error.response) {
      console.warn('Error loading system stats - HTTP status:', error.response.status)
      console.warn('Response data:', error.response.data)
      systemStats.value = defaultStats
      healthScore.value = 0
    } else {
      console.warn('Could not reach system metrics endpoint:', error.message)
      systemStats.value = defaultStats
      healthScore.value = 0
    }
    
    // Always set loading to false on error
    loading.value = false
  }
}

const loadEndpointsStatus = async () => {
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const isOAuthDisabled = import.meta.env.MODE === 'development' && !userStore.user
    const headers = {}
    
    // Only add auth header if we have a token and OAuth is enabled
    if (token && !isOAuthDisabled) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    const endpointsResponse = await axios.get(`${getApiBaseUrl()}/api/admin/system/endpoints`, { 
      headers,
      timeout: 15000 // 15 second timeout for endpoint metrics
    })
    apiEndpoints.value = endpointsResponse.data.data.endpoints
    
    // Load logs after endpoints
    await loadSystemLogs()
  } catch (error) {
    if (error.response?.status !== 404) {
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        console.log('Endpoint metrics request timed out')
      } else {
        console.warn('Could not load endpoint metrics')
      }
    }
    // Fall back to some default endpoints if error
    apiEndpoints.value = [
      {
        method: 'GET',
        path: '/api/health',
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
    const isOAuthDisabled = import.meta.env.MODE === 'development' && !userStore.user
    const headers = {}
    
    // Only add auth header if we have a token and OAuth is enabled
    if (token && !isOAuthDisabled) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    const params = {
      level: logLevel.value,
      limit: 50
    }
    
    const logsResponse = await axios.get(`${getApiBaseUrl()}/api/admin/system/logs`, { 
      headers, 
      params,
      timeout: 15000 // 15 second timeout for logs
    })
    systemLogs.value = logsResponse.data.data.logs
  } catch (error) {
    // Silently keep existing logs if error
    if (error.response?.status !== 404 && error.response?.status !== 401) {
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        console.log('System logs request timed out - using cached logs')
      } else {
        console.log('Using cached logs')
      }
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
  if (!timestamp) return 'Unknown'
  
  try {
    let date
    
    // Handle different timestamp formats
    if (typeof timestamp === 'string') {
      // Try parsing log format: "2025-07-08 11:55:11,166"
      if (timestamp.includes(',')) {
        // Split on comma and parse the main part
        const parts = timestamp.split(',')
        if (parts.length === 2) {
          // Parse the date part and add milliseconds
          const dateStr = parts[0].trim()
          const ms = parts[1].trim()
          
          // Convert to ISO format: "2025-07-08T11:55:11.166Z"
          const isoStr = dateStr.replace(' ', 'T') + '.' + ms.padEnd(3, '0')
          date = new Date(isoStr)
        } else {
          // Fallback to simple replacement
          const cleanTimestamp = timestamp.replace(',', '.')
          date = new Date(cleanTimestamp)
        }
      }
      // Try parsing as ISO string
      else if (timestamp.includes('T') || timestamp.includes('-')) {
        date = new Date(timestamp)
      } 
      // Try parsing simple format
      else {
        date = new Date(timestamp)
      }
    } else if (typeof timestamp === 'number') {
      // Unix timestamp (milliseconds or seconds)
      date = timestamp > 1000000000000 ? new Date(timestamp) : new Date(timestamp * 1000)
    } else {
      date = new Date(timestamp)
    }
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      console.warn('Invalid timestamp format:', timestamp)
      return `Invalid: ${timestamp}`
    }
    
    // Format as readable string
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMinutes = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    
    // Show relative time for recent logs
    if (diffMinutes < 1) {
      return 'Just now'
    } else if (diffMinutes < 60) {
      return `${diffMinutes}m ago`
    } else if (diffHours < 24) {
      return `${diffHours}h ago`
    } else if (diffDays < 7) {
      return `${diffDays}d ago`
    } else {
      // Show full date for older logs
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  } catch (error) {
    console.error('Error formatting timestamp:', error, 'Original:', timestamp)
    return `Error: ${timestamp}`
  }
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

// Log detail methods
const isEndpointFailure = (log) => {
  return log.level === 'error' && (
    log.message.toLowerCase().includes('endpoint') ||
    log.message.toLowerCase().includes('api') ||
    log.message.toLowerCase().includes('failed') ||
    log.statusCode >= 400
  )
}

const hasExpandableDetails = (log) => {
  // Always allow expansion for more details
  return true
}

const toggleLogDetails = (log) => {
  // Toggle expansion state (using Vue's reactivity)
  if (!log.expanded) {
    log.expanded = true
  } else {
    log.expanded = false
  }
}

const getStatusCodeClass = (statusCode) => {
  if (statusCode >= 500) return 'critical'
  if (statusCode >= 400) return 'warning'
  return 'good'
}

const getLogTypeInfo = (log) => {
  const info = {
    icon: '📄',
    description: 'System log entry',
    category: 'General'
  }
  
  if (log.level === 'error') {
    info.icon = '🚨'
    info.category = 'Error'
    if (log.message.toLowerCase().includes('endpoint')) {
      info.description = 'API endpoint failure'
    } else if (log.message.toLowerCase().includes('database')) {
      info.description = 'Database operation error'
    } else {
      info.description = 'System error occurred'
    }
  } else if (log.level === 'warning') {
    info.icon = '⚠️'
    info.category = 'Warning'
    info.description = 'System warning or unusual condition'
  } else if (log.level === 'info') {
    info.icon = 'ℹ️'
    info.category = 'Information'
    if (log.message.toLowerCase().includes('startup')) {
      info.description = 'System startup information'
    } else if (log.message.toLowerCase().includes('connection')) {
      info.description = 'Network connection event'
    } else {
      info.description = 'General system information'
    }
  }
  
  return info
}

const getLogSeverity = (log) => {
  const severityMap = {
    error: { level: 'High', color: 'critical', priority: 3 },
    warning: { level: 'Medium', color: 'warning', priority: 2 },
    info: { level: 'Low', color: 'good', priority: 1 }
  }
  return severityMap[log.level] || severityMap.info
}

const copyLogDetails = async (log) => {
  const details = {
    timestamp: new Date(log.timestamp).toISOString(),
    level: log.level,
    message: log.message,
    context: log.context,
    id: log.id,
    endpoint: log.endpoint,
    statusCode: log.statusCode,
    responseTime: log.responseTime,
    errorDetails: log.errorDetails,
    stackTrace: log.stackTrace
  }
  
  // Remove undefined/null values
  const cleanDetails = Object.fromEntries(
    Object.entries(details).filter(([_, v]) => v != null)
  )
  
  try {
    await navigator.clipboard.writeText(JSON.stringify(cleanDetails, null, 2))
    console.log('✅ Log details copied to clipboard')
    // You could add a toast notification here
  } catch (err) {
    console.error('❌ Failed to copy log details:', err)
    // Fallback: select text for manual copy
    const textArea = document.createElement('textarea')
    textArea.value = JSON.stringify(cleanDetails, null, 2)
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
  }
}

const reportIssue = (log) => {
  console.log('🐛 Reporting issue for log:', log)
  // This could open a modal, create a GitHub issue, or send to an error tracking service
  alert('Issue reporting feature - would integrate with your bug tracking system')
}

// Generate colors for tables
const generateTableColors = (tables) => {
  // High contrast colors with maximum visual distinction
  const colors = [
    '#ff4757', // Red
    '#2ed573', // Green  
    '#3742fa', // Blue
    '#ffa502', // Orange
    '#ff6b9d', // Pink
    '#7bed9f', // Light Green
    '#70a1ff', // Light Blue
    '#ff9f43', // Light Orange
    '#a4b0be', // Gray
    '#5f27cd', // Purple
    '#00d2d3', // Cyan
    '#ff3838', // Bright Red
    '#2f3542', // Dark Gray
    '#ff6b35', // Red Orange
    '#0be881'  // Bright Green
  ]
  const colorMap = {}
  Object.keys(tables).forEach((table, index) => {
    colorMap[table] = colors[index % colors.length]
  })
  return colorMap
}

// Calculate intelligent thresholds based on statistical analysis
const calculateQueryThresholds = (timelineData) => {
  if (!timelineData.length) return { moderate: 0, high: 0, critical: 0 }
  
  // Get all individual table query counts (not totals) for more accurate thresholds
  const allValues = []
  timelineData.forEach(point => {
    Object.values(point.data).forEach(count => {
      if (count > 0) allValues.push(count)
    })
  })
  
  if (allValues.length === 0) return { moderate: 0, high: 0, critical: 0 }
  
  // Calculate statistical measures
  const mean = allValues.reduce((sum, val) => sum + val, 0) / allValues.length
  const sortedValues = [...allValues].sort((a, b) => a - b)
  const median = sortedValues[Math.floor(sortedValues.length / 2)]
  const q75 = sortedValues[Math.floor(sortedValues.length * 0.75)]
  const q90 = sortedValues[Math.floor(sortedValues.length * 0.90)]
  const max = Math.max(...allValues)
  const min = Math.min(...allValues)
  
  // Calculate standard deviation
  const variance = allValues.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / allValues.length
  const stdDev = Math.sqrt(variance)
  
  // Use much more conservative thresholds to avoid false alarms
  
  // For very low query volumes, don't highlight anything unless there's a dramatic spike
  if (max <= 5) {
    return {
      moderate: max * 5,      // 5x the maximum observed
      high: max * 10,         // 10x the maximum observed  
      critical: max * 20,     // 20x the maximum observed
      stats: { mean: Math.round(mean), median: Math.round(median), stdDev: Math.round(stdDev) }
    }
  }
  
  // For moderate volumes, use very conservative multiples
  if (max <= 20) {
    return {
      moderate: Math.round(max * 2.5),   // 2.5x max
      high: Math.round(max * 4),         // 4x max
      critical: Math.round(max * 6),     // 6x max
      stats: { mean: Math.round(mean), median: Math.round(median), stdDev: Math.round(stdDev) }
    }
  }
  
  // For higher volumes, use statistical analysis but be conservative
  const moderate = Math.round(Math.max(
    q90 * 1.5,              // 1.5x 90th percentile
    mean + (3 * stdDev),    // 3 standard deviations above mean
    max * 1.2               // 20% above maximum
  ))
  
  const high = Math.round(Math.max(
    q90 * 2,                // 2x 90th percentile
    mean + (4 * stdDev),    // 4 standard deviations above mean
    max * 1.5               // 50% above maximum
  ))
  
  const critical = Math.round(Math.max(
    q90 * 3,                // 3x 90th percentile
    mean + (5 * stdDev),    // 5 standard deviations above mean
    max * 2                 // 2x maximum
  ))
  
  return {
    moderate: Math.round(moderate),
    high: Math.round(high),
    critical: Math.round(critical),
    stats: { mean: Math.round(mean), median: Math.round(median), stdDev: Math.round(stdDev) }
  }
}

// Draw query timeline chart
const drawQueryTimeline = () => {
  if (!queryTimelineChart.value) {
    return
  }
  
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
  
  if (!timelineData || timelineData.length === 0) {
    // Draw empty state message
    ctx.fillStyle = '#6b7280'
    ctx.font = '16px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('No query data available', width / 2, height / 2)
    ctx.font = '12px sans-serif'
    ctx.fillText('Data will appear as queries are executed', width / 2, height / 2 + 20)
    return
  }
  
  // Find max value for scaling
  const maxValue = Math.max(...timelineData.flatMap(point => 
    Object.values(point.data).reduce((sum, val) => sum + val, 0)
  )) || 1
  
  // If maxValue is 0 or very small, show minimal data message
  if (maxValue <= 1) {
    ctx.fillStyle = '#6b7280'
    ctx.font = '14px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('Minimal query activity', width / 2, height / 2 - 10)
    ctx.font = '12px sans-serif'
    ctx.fillText('Chart will display meaningful data as more queries are executed', width / 2, height / 2 + 10)
    return
  }
  
  // Calculate intelligent thresholds
  const thresholds = calculateQueryThresholds(timelineData)
  
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
    ctx.lineWidth = 3
    ctx.beginPath()
    
    const points = []
    timelineData.forEach((point, index) => {
      // Handle single data point case
      const x = timelineData.length === 1 ? 
        padding + chartWidth / 2 : 
        padding + (index / (timelineData.length - 1)) * chartWidth
      const y = padding + chartHeight - (point.data[table] || 0) / maxValue * chartHeight
      points.push({ x, y, value: point.data[table] || 0 })
      
      if (index === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    })
    
    ctx.stroke()
    
    // Draw data points
    ctx.fillStyle = color
    points.forEach(point => {
      ctx.beginPath()
      ctx.arc(point.x, point.y, 4, 0, Math.PI * 2)
      ctx.fill()
      
      // Highlight query points based on conservative thresholds (only for significant spikes)
      if (point.value >= thresholds.critical) {
        // Critical threshold - bright red
        ctx.strokeStyle = '#ff4757'
        ctx.lineWidth = 3
        ctx.beginPath()
        ctx.arc(point.x, point.y, 10, 0, Math.PI * 2)
        ctx.stroke()
      } else if (point.value >= thresholds.high) {
        // High threshold - orange
        ctx.strokeStyle = '#ffa502'
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.arc(point.x, point.y, 8, 0, Math.PI * 2)
        ctx.stroke()
      } else if (point.value >= thresholds.moderate) {
        // Moderate threshold - yellow
        ctx.strokeStyle = '#ffda79'
        ctx.lineWidth = 1
        ctx.beginPath()
        ctx.arc(point.x, point.y, 6, 0, Math.PI * 2)
        ctx.stroke()
      }
    })
  })
  
  // Draw time scale indicator
  ctx.fillStyle = '#667eea'
  ctx.font = 'bold 14px sans-serif'
  ctx.textAlign = 'right'
  ctx.fillText(`${selectedTimeScale.value.toUpperCase()} (${timelineData.length} points)`, padding + chartWidth, padding - 10)
  
  // Draw axis labels
  ctx.fillStyle = '#d1d5db'
  ctx.font = '12px sans-serif'
  
  // X-axis title
  ctx.textAlign = 'center'
  ctx.fillText('Time', padding + chartWidth / 2, height - 5)
  
  // Y-axis title
  ctx.save()
  ctx.translate(15, padding + chartHeight / 2)
  ctx.rotate(-Math.PI / 2)
  ctx.fillText('Query Count', 0, 0)
  ctx.restore()
  
  // X-axis labels
  ctx.fillStyle = '#9ca3af'
  ctx.font = '11px sans-serif'
  ctx.textAlign = 'center'
  
  if (timelineData.length === 1) {
    // Single point - center the label
    ctx.fillText(timelineData[0].time, padding + chartWidth / 2, height - 25)
  } else {
    // Multiple points - distribute labels
    const labelInterval = Math.max(1, Math.ceil(timelineData.length / 4))
    timelineData.forEach((point, index) => {
      if (index % labelInterval === 0 || index === timelineData.length - 1) {
        const x = padding + (index / (timelineData.length - 1)) * chartWidth
        ctx.fillText(point.time, x, height - 25)
      }
    })
  }
  
  // Add threshold lines based on intelligent analysis
  // Only show threshold lines if they would be meaningful and visible
  const showThresholds = thresholds.moderate > 0 && maxValue > 5
  const maxDisplayThreshold = maxValue * 2 // Don't show lines more than 2x the current max
  
  if (showThresholds) {
    // Only show critical threshold line if it's reasonable and visible
    if (thresholds.critical > 0 && thresholds.critical <= maxDisplayThreshold && thresholds.critical > maxValue * 1.1) {
      const criticalY = padding + chartHeight - (thresholds.critical / maxValue) * chartHeight
      ctx.strokeStyle = '#ff4757'
      ctx.lineWidth = 1
      ctx.setLineDash([8, 3])
      ctx.beginPath()
      ctx.moveTo(padding, criticalY)
      ctx.lineTo(padding + chartWidth, criticalY)
      ctx.stroke()
      ctx.setLineDash([])
      
      // Critical threshold label
      ctx.fillStyle = '#ff4757'
      ctx.font = '9px sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(`Critical (${thresholds.critical})`, padding + 5, criticalY - 5)
    }
    
    // Only show high threshold line if it's reasonable and different from critical
    if (thresholds.high > 0 && 
        thresholds.high <= maxDisplayThreshold && 
        thresholds.high > maxValue * 1.05 && 
        thresholds.high < thresholds.critical * 0.9) {
      const highY = padding + chartHeight - (thresholds.high / maxValue) * chartHeight
      ctx.strokeStyle = '#ffa502'
      ctx.lineWidth = 1
      ctx.setLineDash([5, 3])
      ctx.beginPath()
      ctx.moveTo(padding, highY)
      ctx.lineTo(padding + chartWidth, highY)
      ctx.stroke()
      ctx.setLineDash([])
      
      // High threshold label
      ctx.fillStyle = '#ffa502'
      ctx.font = '9px sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(`High (${thresholds.high})`, padding + 5, highY - 5)
    }
  }
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
  
  // Determine how many entries to include based on time scale  
  let entriesToInclude = timeline.length // Start with all available data
  if (selectedTimeScale.value === '1h') {
    entriesToInclude = 1 // Always show only the most recent entry
  } else if (selectedTimeScale.value === '6h') {
    entriesToInclude = Math.min(3, timeline.length) // Show last 3 hours for visual difference
  } else if (selectedTimeScale.value === '24h') {
    entriesToInclude = Math.min(5, timeline.length) // Show last 5 entries
  } else if (selectedTimeScale.value === '7d') {
    entriesToInclude = timeline.length // Show all available data
  }
  
  // Get the relevant timeline entries
  const relevantEntries = timeline.slice(-entriesToInclude)
  
  // Process entries based on time scale
  relevantEntries.forEach((entry, index) => {
    let timeLabel
    
    if (selectedTimeScale.value === '1h') {
      timeLabel = 'Now'
    } else if (selectedTimeScale.value === '7d') {
      // For 7-day view, show date
      const date = new Date(entry.timestamp)
      timeLabel = date.toLocaleDateString([], { month: 'short', day: 'numeric' })
    } else {
      // For hourly views (6h, 24h), show relative time
      const hoursAgo = relevantEntries.length - index - 1
      timeLabel = hoursAgo === 0 ? 'Now' : `-${hoursAgo}h`
    }
    
    let data = entry.tables || {}
    // If no table-specific data, use total as a general metric
    if (Object.keys(data).length === 0 && entry.total_queries > 0) {
      data = { 'queries': entry.total_queries }
    }
    
    points.push({
      time: timeLabel,
      data: data
    })
  })
  
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

// Reset database performance metrics
const resetDatabaseMetrics = async () => {
  try {
    isResetting.value = true
    
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
    
    console.log('Resetting database performance metrics...')
    
    const response = await axios.post(`${getApiBaseUrl()}/api/admin/system/metrics/reset`, {}, { 
      headers,
      timeout: 10000
    })
    
    if (response.data.success) {
      console.log('Database metrics reset successfully')
      
      // Show success notification
      notificationStore.addNotification({
        type: 'success',
        title: 'Metrics Reset',
        message: 'Database performance metrics have been reset successfully'
      })
      
      // Refresh the metrics data
      await loadSystemStats()
      
    } else {
      throw new Error(response.data.message || 'Reset failed')
    }
    
  } catch (error) {
    console.error('Error resetting database metrics:', error)
    
    notificationStore.addNotification({
      type: 'error',
      title: 'Reset Failed',
      message: error.response?.data?.message || error.message || 'Failed to reset database metrics'
    })
  } finally {
    isResetting.value = false
    showResetConfirmation.value = false
  }
}

// Show table breakdown modal
const showTableBreakdown = async (tableName) => {
  try {
    console.log(`Fetching query breakdown for table: ${tableName}`)
    
    // Set up modal
    selectedTable.value = tableName
    showTableModal.value = true
    tableBreakdownLoading.value = true
    tableBreakdown.value = {}
    
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const headers = {
      'Authorization': `Bearer ${token}`
    }
    
    const response = await axios.get(`${getApiBaseUrl()}/api/admin/database/table-sources/${tableName}`, { 
      headers,
      timeout: 15000 // Increased timeout to match other endpoints
    })
    
    const data = response.data.data
    tableBreakdown.value = data
    
  } catch (error) {
    console.error('Error fetching table breakdown:', error)
    tableBreakdown.value = {
      table_name: tableName,
      total_queries: 0,
      sources: [],
      error: error.message
    }
  } finally {
    tableBreakdownLoading.value = false
  }
}

// Close table breakdown modal
const closeTableModal = () => {
  showTableModal.value = false
  selectedTable.value = ''
  tableBreakdown.value = {}
}

// Lifecycle
onMounted(() => {
  // Check authentication first
  if (!userStore.isAuthenticated || userStore.user?.role !== 'admin') {
    console.log('User not authenticated or not admin, redirecting to admin login')
    router.push('/admin')
    return
  }
  
  console.log('User authenticated as admin, loading system stats')
  // Load data with error handling
  loadSystemStats().catch(err => {
    console.error('Failed to load system stats:', err)
    // Set offline mode
    heartbeatStatus.value = 'Offline'
    healthScore.value = 0
  })
  
  // Re-enable auto-refresh with longer intervals to reduce load
  console.log('🔄 Starting auto-refresh every 5 seconds')
  updateInterval = setInterval(() => {
    loadSystemStats().catch(err => {
      console.error('Failed to refresh system stats:', err)
    })
  }, 5000)  // Update every 5 seconds for more real-time monitoring
  
  // Re-enable heartbeat monitoring with longer intervals
  console.log('🫀 Starting heartbeat monitoring every 30 seconds (reduced frequency)')
  checkHeartbeat().catch(err => {
    console.error('Initial heartbeat check failed:', err)
    heartbeatStatus.value = 'Offline'
  })
  heartbeatInterval = setInterval(() => {
    checkHeartbeat().catch(err => {
      console.error('Heartbeat check failed:', err)
    })
  }, 30000)  // Increased from 15s to 30s
})

onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval)
  }
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval)
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

/* Heartbeat Status Styles */
.heartbeat-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.heartbeat-dot {
  font-size: 0.8rem;
  animation: pulse 2s infinite;
}

.heartbeat-dot.good {
  color: #10b981;
}

.heartbeat-dot.warning {
  color: #f59e0b;
}

.heartbeat-dot.critical {
  color: #ef4444;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
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
  max-height: 450px;
  overflow-y: auto;
  background: rgba(15, 15, 30, 0.5);
  border-radius: 8px;
  padding: 0;
  border: 1px solid rgba(102, 126, 234, 0.1);
  position: relative;
}

.logs-header-row {
  display: grid;
  grid-template-columns: 150px 80px 1fr;
  gap: 15px;
  padding: 12px;
  background: rgba(102, 126, 234, 0.1);
  border-bottom: 2px solid rgba(102, 126, 234, 0.2);
  font-weight: 600;
  color: #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-time,
.header-level,
.header-message {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.header-time {
  color: #9ca3af;
}

.header-level {
  color: #9ca3af;
  text-align: center;
}

.header-message {
  color: #e5e7eb;
  text-align: center;
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
  margin: 0;
  border-radius: 0;
}

.log-entry:hover {
  background: rgba(102, 126, 234, 0.1);
}

.log-entry:last-child {
  border-bottom: none;
}

.log-entry.expandable {
  cursor: pointer;
}

.log-entry.endpoint-failure {
  border-left: 4px solid #ef4444;
  background: rgba(239, 68, 68, 0.05);
  margin-left: 0;
}

.log-entry.endpoint-failure:hover {
  background: rgba(239, 68, 68, 0.1);
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

.log-message {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.message-text {
  flex: 1;
}

.endpoint-failure-badge {
  background: #ef4444;
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
}

.expand-icon {
  transition: transform 0.2s;
  color: #9ca3af;
  font-size: 0.8rem;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.log-details {
  margin-top: 12px;
  padding: 0;
  background: rgba(15, 15, 30, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.2);
  font-size: 0.8rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  animation: slideDown 0.3s ease-out;
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

.detail-section {
  padding: 16px;
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
}

.detail-section:last-child {
  border-bottom: none;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: #667eea;
}

.section-icon {
  font-size: 1rem;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.detail-item.full-width {
  grid-column: 1 / -1;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-grid .detail-item {
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.detail-label {
  font-weight: 600;
  color: #9ca3af;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  min-width: 100px;
  flex-shrink: 0;
}

.detail-value {
  color: #e5e7eb;
  word-break: break-word;
  line-height: 1.4;
}

.detail-value.good {
  color: #10b981;
  font-weight: 500;
}

.detail-value.warning {
  color: #f59e0b;
  font-weight: 500;
}

.detail-value.critical {
  color: #ef4444;
  font-weight: 500;
}

.detail-value.timestamp {
  font-family: 'Consolas', 'Monaco', monospace;
  background: rgba(102, 126, 234, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.75rem;
}

.message-content {
  background: rgba(30, 30, 50, 0.6);
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid #667eea;
  font-family: 'Consolas', 'Monaco', monospace;
  white-space: pre-wrap;
  font-size: 0.8rem;
  line-height: 1.5;
}

.context-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 0.75rem;
  font-weight: 500;
  display: inline-block;
}

.endpoint-badge {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
}

.detail-value.error-details,
.detail-value.stack-trace {
  background: rgba(239, 68, 68, 0.1);
  padding: 12px;
  border-radius: 6px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.75rem;
  white-space: pre-wrap;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid rgba(239, 68, 68, 0.2);
  line-height: 1.4;
  margin-top: 8px;
}

.detail-actions {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: rgba(30, 30, 50, 0.4);
  border-radius: 0 0 8px 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn {
  background: rgba(102, 126, 234, 0.2);
  color: #667eea;
  border: 1px solid rgba(102, 126, 234, 0.3);
}

.copy-btn:hover {
  background: rgba(102, 126, 234, 0.3);
  border-color: rgba(102, 126, 234, 0.5);
}

.report-btn {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.report-btn:hover {
  background: rgba(239, 68, 68, 0.3);
  border-color: rgba(239, 68, 68, 0.5);
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
  min-height: 60px;
}

.table-item:hover {
  background: rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.3);
}

.table-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0; /* Allows text to wrap if needed */
}

.table-name {
  font-weight: 500;
  color: #e5e7eb;
  text-transform: lowercase;
  font-size: 0.95rem;
  line-height: 1.2;
}

.table-count {
  color: #667eea;
  font-weight: 600;
  font-size: 0.85rem;
  opacity: 0.9;
}

.table-arrow {
  color: #667eea;
  font-weight: bold;
  margin-left: 12px;
  opacity: 0.7;
  transition: all 0.2s;
}

.table-item:hover .table-arrow {
  opacity: 1;
  transform: translateX(2px);
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
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(102, 126, 234, 0.1);
}

.legend-title {
  color: #e5e7eb;
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 10px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
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

/* Timeline legends container */
.timeline-legends {
  display: flex;
  justify-content: space-between;
  gap: 30px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(102, 126, 234, 0.1);
}

.timeline-legends .timeline-legend {
  flex: 1;
  margin-top: 0;
  padding-top: 0;
  border-top: none;
}

/* Threshold color styles for query load legend */
.legend-color.threshold-normal {
  background-color: #10b981; /* Green for normal */
}

.legend-color.threshold-moderate {
  background-color: #ffda79; /* Yellow for moderate */
}

.legend-color.threshold-high {
  background-color: #ffa502; /* Orange for high */
}

.legend-color.threshold-critical {
  background-color: #ff4757; /* Red for critical */
}

/* Ring styles for query load thresholds (matching graph indicators) */
.legend-ring {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border-width: 2px;
  border-style: solid;
  background-color: transparent;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.legend-ring.threshold-normal {
  border-color: #10b981; /* Green ring for normal */
}

.legend-ring.threshold-moderate {
  border-color: #ffda79; /* Yellow ring for moderate */
}

.legend-ring.threshold-high {
  border-color: #ffa502; /* Orange ring for high */
}

.legend-ring.threshold-critical {
  border-color: #ff4757; /* Red ring for critical */
}

/* Responsive adjustments for legends */
@media (max-width: 768px) {
  .timeline-legends {
    flex-direction: column;
    gap: 20px;
  }
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

/* Modal Styles */
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
  padding: 20px;
}

.modal-content {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(45, 55, 72, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  max-width: 700px;
  width: 100%;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h3 {
  margin: 0;
  color: #e5e7eb;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  color: #e5e7eb;
  background: rgba(255, 255, 255, 0.1);
}

.modal-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  min-height: 0; /* Important for flexbox scrolling */
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #9ca3af;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(102, 126, 234, 0.3);
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.breakdown-summary {
  margin-bottom: 20px;
  padding: 15px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.breakdown-summary p {
  margin: 0;
  color: #e5e7eb;
  font-size: 1rem;
}

.breakdown-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 8px; /* Space for scrollbar */
}

.source-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 15px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: background 0.2s;
}

.source-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.source-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.source-endpoint {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9rem;
  color: #e5e7eb;
  font-weight: 500;
}

.source-count {
  font-size: 0.85rem;
  color: #9ca3af;
  font-weight: 500;
}

.source-bar {
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.source-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.no-data, .error-state {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
}

.error-state {
  color: #ef4444;
}

.error-state p {
  margin: 0;
}

/* Custom scrollbar styles */
.breakdown-list::-webkit-scrollbar {
  width: 6px;
}

.breakdown-list::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.breakdown-list::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.6);
  border-radius: 3px;
}

.breakdown-list::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.8);
}

.modal-body::-webkit-scrollbar {
  width: 6px;
}

.modal-body::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.6);
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.8);
}

/* Section header styles */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  margin: 0;
}

/* Reset button styles */
.reset-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #dc3545, #c82333);
  border: none;
  border-radius: 0.5rem;
  color: white;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
}

.reset-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #c82333, #a71e2a);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.4);
}

.reset-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Reset confirmation modal styles */
.warning-text {
  color: #f59e0b;
  font-weight: 500;
  margin: 1rem 0 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.reset-list {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0 1rem 1.5rem;
}

.reset-list li {
  padding: 0.25rem 0;
  position: relative;
}

.reset-list li::before {
  content: '•';
  color: #f59e0b;
  position: absolute;
  left: -1rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.cancel-button {
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.5rem;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cancel-button:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

.confirm-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #dc3545, #c82333);
  border: none;
  border-radius: 0.5rem;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.confirm-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #c82333, #a71e2a);
}

.confirm-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>