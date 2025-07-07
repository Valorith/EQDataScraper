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
            <span class="stat-value" :class="scrapingStatus.active ? 'warning' : 'info'">
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
          <button @click="navigateToSystem" class="action-button primary">
            <i class="fas fa-arrow-right"></i>
            System Details
          </button>
        </div>
      </div>

      <!-- Content Database Card -->
      <div class="dashboard-card">
        <div class="card-header">
          <div class="card-icon database" :class="{
            'status-connected': databaseStatus.connected,
            'status-disconnected': !databaseStatus.connected
          }">
            <i class="fas" :class="databaseStatus.connected ? 'fa-check-circle' : 'fa-exclamation-circle'"></i>
          </div>
          <h2>Content Database</h2>
        </div>
        <div class="card-content">
          <div class="stat-row">
            <span class="stat-label">Status</span>
            <span class="stat-value" :class="databaseStatus.connected ? 'success' : 'warning'">
              {{ databaseStatus.connected ? 'Connected' : 'Disconnected' }}
            </span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Host</span>
            <span class="stat-value">{{ databaseStatus.host || 'Not configured' }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Database</span>
            <span class="stat-value">{{ databaseStatus.database || 'None' }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Config Source</span>
            <span class="stat-value" :class="{
              'success': storageInfo.config_source === 'persistent_storage',
              'info': storageInfo.config_source === 'environment_variable',
              'warning': storageInfo.config_source === 'config_json' || storageInfo.config_source === 'none'
            }">
              {{ formatConfigSource(storageInfo.config_source) }}
            </span>
          </div>
          <div v-if="storageInfo.config_source === 'none'" class="stat-row warning-row">
            <i class="fas fa-exclamation-triangle"></i>
            <span class="warning-text">Database configuration will be lost on deployment!</span>
          </div>
        </div>
        <div class="card-actions database-actions">
          <button @click="openDatabaseModal" class="action-button primary">
            <i class="fas fa-cog"></i>
            Configure
          </button>
          <button @click="openDiagnosticsModal" class="action-button secondary">
            <i class="fas fa-stethoscope"></i>
            Diagnose
          </button>
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

    <!-- Network Test Modal -->
    <div v-if="showNetworkTestModal" class="modal-overlay" @click.self="closeNetworkTestModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Network Connectivity Test</h2>
          <button @click="closeNetworkTestModal" class="close-button">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <p class="modal-description">
            Test network connectivity from Railway to various hosts to diagnose connection issues.
          </p>
          
          <div class="form-group">
            <label for="test-host">Host (IP or Domain)</label>
            <input 
              id="test-host"
              v-model="networkTestForm.host" 
              type="text" 
              placeholder="e.g., 8.8.8.8 or google.com"
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label for="test-port">Port</label>
            <input 
              id="test-port"
              v-model.number="networkTestForm.port" 
              type="number" 
              placeholder="3306"
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label for="test-type">Test Type</label>
            <select id="test-type" v-model="networkTestForm.test_type" class="form-input">
              <option value="tcp">TCP Connection</option>
              <option value="ping">ICMP Ping</option>
              <option value="mysql">MySQL Connection</option>
            </select>
          </div>
          
          <!-- Quick test buttons -->
          <div class="quick-tests">
            <p>Quick Tests:</p>
            <button @click="setQuickTest('76.251.85.36', 3306, 'tcp')" class="quick-test-btn">
              Your SQL Server
            </button>
            <button @click="setQuickTest('8.8.8.8', 53, 'tcp')" class="quick-test-btn">
              Google DNS
            </button>
            <button @click="setQuickTest('1.1.1.1', 53, 'tcp')" class="quick-test-btn">
              Cloudflare DNS
            </button>
            <button @click="setQuickTest('google.com', 80, 'tcp')" class="quick-test-btn">
              Google.com
            </button>
          </div>
          
          <!-- Test Results -->
          <div v-if="networkTestResult" class="test-results" :class="{ 'success': networkTestResult.overall_success, 'error': !networkTestResult.overall_success }">
            <h3>Test Results for {{ networkTestResult.host }}:{{ networkTestResult.port }}</h3>
            
            <div v-for="(test, name) in networkTestResult.tests" :key="name" class="test-item">
              <div class="test-header">
                <i class="fas" :class="test.success ? 'fa-check-circle' : 'fa-times-circle'"></i>
                <strong>{{ formatTestName(name) }}</strong>
                <span v-if="test.time_ms" class="test-time">({{ test.time_ms }}ms)</span>
              </div>
              <div class="test-message">{{ test.message }}</div>
              <div v-if="test.error" class="test-error">
                Error: {{ test.error_type || 'Unknown' }} - {{ test.error }}
              </div>
              <div v-if="test.resolved_addresses" class="test-detail">
                Resolved IPs: {{ test.resolved_addresses.join(', ') }}
              </div>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button 
            @click="runNetworkTest" 
            class="primary-button"
            :disabled="testingNetwork || !networkTestForm.host"
          >
            <i class="fas" :class="testingNetwork ? 'fa-spinner fa-spin' : 'fa-network-wired'"></i>
            {{ testingNetwork ? 'Testing...' : 'Run Test' }}
          </button>
          <button @click="closeNetworkTestModal" class="secondary-button">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- Database Diagnostics Modal -->
    <div v-if="showDiagnosticsModal" class="modal-overlay" @click.self="closeDiagnosticsModal">
      <div class="modal-content diagnostics-modal">
        <div class="modal-header">
          <h2>Database Diagnostics</h2>
          <button @click="closeDiagnosticsModal" class="close-button">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <p class="modal-description">
            Run various diagnostic tests to troubleshoot database connection issues.
          </p>
          
          <!-- Test Options -->
          <div class="diagnostic-tests">
            <div class="test-card">
              <div class="test-header">
                <i class="fas fa-sync-alt"></i>
                <h3>Refresh Connection</h3>
              </div>
              <p>Attempt to reconnect to the database using stored configuration.</p>
              <button 
                @click="refreshConnection" 
                class="test-button"
                :disabled="refreshingConnection"
              >
                <i class="fas fa-sync-alt" :class="{ 'fa-spin': refreshingConnection }"></i>
                {{ refreshingConnection ? 'Refreshing...' : 'Refresh Connection' }}
              </button>
            </div>
            
            <div class="test-card">
              <div class="test-header">
                <i class="fas fa-clipboard-check"></i>
                <h3>Full Diagnostics</h3>
              </div>
              <p>Run comprehensive diagnostics including environment checks, configuration validation, and connection tests.</p>
              <button 
                @click="runDiagnostics" 
                class="test-button"
                :disabled="runningDiagnostics"
              >
                <i class="fas fa-clipboard-check" :class="{ 'fa-spin': runningDiagnostics }"></i>
                {{ runningDiagnostics ? 'Running...' : 'Run Full Diagnostics' }}
              </button>
            </div>
            
            <div class="test-card">
              <div class="test-header">
                <i class="fas fa-network-wired"></i>
                <h3>Network Test</h3>
              </div>
              <p>Test network connectivity to various hosts to isolate connection issues.</p>
              <button 
                @click="openNetworkTest" 
                class="test-button"
              >
                <i class="fas fa-network-wired"></i>
                Open Network Test
              </button>
            </div>
          </div>
          
          <!-- Diagnostics Results -->
          <div v-if="diagnosticsResult" class="diagnostics-result">
            <h3>Diagnostics Report</h3>
            <div class="result-content">
              <pre>{{ diagnosticsResult }}</pre>
            </div>
          </div>
          
          <!-- Connection Status -->
          <div v-if="connectionTestResult" class="connection-result" :class="connectionTestResult.success ? 'success' : 'error'">
            <div class="result-header">
              <i class="fas" :class="connectionTestResult.success ? 'fa-check-circle' : 'fa-times-circle'"></i>
              <strong>{{ connectionTestResult.message }}</strong>
            </div>
            <div v-if="connectionTestResult.details" class="result-details">
              {{ connectionTestResult.details }}
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="closeDiagnosticsModal" class="secondary-button">
            Close
          </button>
        </div>
      </div>
    </div>

    <!-- Database Configuration Modal -->
    <div v-if="showDatabaseModal" class="modal-overlay" @click="closeDatabaseModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Database Configuration</h3>
          <button @click="closeDatabaseModal" class="modal-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <form @submit.prevent="saveDatabaseConfig">
            <div class="form-group">
              <label for="db-type">Database Type</label>
              <select 
                id="db-type"
                v-model="databaseForm.db_type" 
                @change="updateDefaultPort"
                class="form-input"
                required
              >
                <option value="mssql">Microsoft SQL Server</option>
                <option value="mysql">MySQL</option>
                <option value="postgresql">PostgreSQL</option>
              </select>
            </div>
            
            <div class="form-group">
              <label for="db-host">Host</label>
              <input 
                id="db-host"
                v-model="databaseForm.host" 
                type="text" 
                class="form-input"
                placeholder="localhost"
                required
              />
            </div>
            
            <div class="form-group">
              <label for="db-port">Port</label>
              <input 
                id="db-port"
                v-model="databaseForm.port" 
                type="number" 
                class="form-input"
                placeholder="5432"
                min="1"
                max="65535"
                required
              />
            </div>
            
            <div class="form-group">
              <label for="db-name">Database Name</label>
              <input 
                id="db-name"
                v-model="databaseForm.database" 
                type="text" 
                class="form-input"
                placeholder="eqdata"
                required
              />
            </div>
            
            <div class="form-group">
              <label for="db-username">Username</label>
              <input 
                id="db-username"
                v-model="databaseForm.username" 
                type="text" 
                class="form-input"
                placeholder="postgres"
                required
              />
            </div>
            
            <div class="form-group">
              <label for="db-password">Password</label>
              <input 
                id="db-password"
                v-model="databaseForm.password" 
                type="password" 
                class="form-input"
                placeholder="Enter password"
                required
              />
            </div>
            
            <div class="form-group checkbox-group">
              <label class="checkbox-label">
                <input 
                  v-model="databaseForm.use_ssl" 
                  type="checkbox" 
                  class="form-checkbox"
                />
                <span class="checkbox-text">Use SSL Connection</span>
              </label>
            </div>
            
            <div v-if="databaseTestResult" class="test-result" :class="databaseTestResult.success ? 'success' : 'error'">
              <i :class="databaseTestResult.success ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
              <span>{{ databaseTestResult.message }}</span>
              
              <!-- Success details -->
              <div v-if="databaseTestResult.success && databaseTestResult.data" class="test-details">
                <p v-if="databaseTestResult.data.read_only_mode">✓ Read-only mode enabled</p>
                <p v-if="databaseTestResult.data.tables">
                  ✓ Items table: {{ databaseTestResult.data.tables.items_accessible ? 'Accessible' : 'Not accessible' }}
                  <span v-if="databaseTestResult.data.tables.items_count">({{ databaseTestResult.data.tables.items_count }} items)</span>
                </p>
                <p v-if="databaseTestResult.data.tables">
                  ✓ Discovered items table: {{ databaseTestResult.data.tables.discovered_items_accessible ? 'Accessible' : 'Not accessible' }}
                  <span v-if="databaseTestResult.data.tables.discovered_items_count">({{ databaseTestResult.data.tables.discovered_items_count }} discovered)</span>
                </p>
              </div>
              
              <!-- Error details -->
              <div v-if="!databaseTestResult.success && databaseTestResult.error" class="error-details">
                <div class="error-issue">
                  <strong>Issue:</strong> {{ databaseTestResult.error.details?.issue || 'Unknown error' }}
                </div>
                <div class="error-suggestion">
                  <strong>Suggestion:</strong> {{ databaseTestResult.error.details?.suggestion || 'Please check your connection details' }}
                </div>
                <div v-if="databaseTestResult.error.error_message" class="error-technical">
                  <details>
                    <summary>Technical details</summary>
                    <code>{{ databaseTestResult.error.error_message }}</code>
                  </details>
                </div>
              </div>
            </div>
          </form>
        </div>
        
        <div class="modal-footer">
          <button 
            @click="testDatabaseConnection" 
            class="test-button"
            :disabled="testingConnection"
          >
            <i class="fas fa-plug" :class="{ 'fa-spin': testingConnection }"></i>
            {{ testingConnection ? 'Testing...' : 'Test Connection' }}
          </button>
          
          <button 
            @click="saveDatabaseConfig" 
            class="save-button"
            :disabled="savingConfig || !databaseTestResult?.success"
          >
            <i class="fas fa-save" :class="{ 'fa-spin': savingConfig }"></i>
            {{ savingConfig ? 'Saving...' : 'Save Configuration' }}
          </button>
          
          <button @click="closeDatabaseModal" class="cancel-button">
            Cancel
          </button>
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

// Database configuration state
const showDatabaseModal = ref(false)
const databaseStatus = ref({
  connected: false,
  host: null,
  database: null,
  status: 'unknown'
})

// Network test state
const showNetworkTestModal = ref(false)
const testingNetwork = ref(false)
const networkTestResult = ref(null)
const networkTestForm = ref({
  host: '',
  port: 3306,
  test_type: 'tcp',
  username: '',
  password: '',
  database: ''
})

// Diagnostics modal state
const showDiagnosticsModal = ref(false)
const connectionTestResult = ref(null)
const storageInfo = ref({
  config_source: 'unknown',
  storage_available: false,
  directory_writable: false,
  data_directory: null
})
const databaseForm = ref({
  db_type: 'mssql',
  host: '',
  port: 1433,
  database: '',
  username: '',
  password: '',
  use_ssl: true
})
const databaseTestResult = ref(null)
const testingConnection = ref(false)
const savingConfig = ref(false)
const refreshingConnection = ref(false)
const runningDiagnostics = ref(false)

let refreshInterval = null
let activityRefreshInterval = null

// Methods
const loadDashboardData = async () => {
  // Silently load dashboard data
  
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
      console.log('Admin stats require authentication')
    } else if (error.response?.status === 403) {
      console.log('Admin stats require admin privileges')
    } else if (error.response?.status === 404) {
      console.log('Admin stats endpoint not found - OAuth may be disabled')
    } else if (error.response) {
      console.warn('Error loading stats:', error.response.status, error.response.data?.message || '')
    } else if (error.request) {
      console.warn('No response from server when loading stats')
    } else {
      console.warn('Error setting up stats request:', error.message)
    }
    // Set default values
    stats.value = { totalUsers: 0, activeToday: 0, adminUsers: 0 }
  }

  // Load database configuration status
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const dbConfigRes = await axios.get(`${API_BASE_URL}/api/admin/database/config`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    if (dbConfigRes.data.success && dbConfigRes.data.data?.database) {
      const dbData = dbConfigRes.data.data.database
      databaseStatus.value = {
        connected: dbData.connected || false,
        host: dbData.host || null,
        port: dbData.port || null,
        database: dbData.database || null,
        username: dbData.username || null,
        db_type: dbData.db_type || null,
        use_ssl: dbData.use_ssl !== undefined ? dbData.use_ssl : true,
        status: dbData.status || 'unknown',
        version: dbData.version || null,
        connection_type: dbData.connection_type || 'unknown'
      }
      
      // Update storage info if available
      if (dbConfigRes.data.data?.storage_info) {
        storageInfo.value = {
          config_source: dbConfigRes.data.data.storage_info.config_source || 'unknown',
          storage_available: dbConfigRes.data.data.storage_info.storage_available || false,
          directory_writable: dbConfigRes.data.data.storage_info.directory_writable || false,
          data_directory: dbConfigRes.data.data.storage_info.data_directory || null
        }
      }
    } else {
      // No database configured
      databaseStatus.value = {
        connected: false,
        host: null,
        port: null,
        database: null,
        username: null,
        db_type: null,
        use_ssl: true,
        status: 'not_configured',
        connection_type: 'none'
      }
    }
  } catch (error) {
    if (error.response?.status === 404) {
      console.log('Database config endpoint not found - OAuth may be disabled')
    } else if (error.response?.status === 401 || error.response?.status === 403) {
      console.log('Database config requires admin authentication')
    } else if (error.response) {
      console.warn('Error loading database config:', error.response.status)
    } else {
      console.warn('Could not reach database config endpoint')
    }
    // Set default values
    databaseStatus.value = {
      connected: false,
      host: null,
      database: null,
      status: 'error'
    }
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
    
    // If all classes are cached but no update time found, don't set a fake time
    // This prevents confusion about when the cache was actually last updated
    if (totalCached > 0 && !lastUpdate) {
      // Keep lastUpdate as null instead of faking it
      lastUpdate = null
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
    if (!error.response || error.response.status !== 404) {
      console.warn('Error loading cache status:', error.message)
    }
    
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
      console.warn('Cache status endpoints not available')
      cacheStatus.value = { healthy: false, cachedClasses: 0, lastUpdate: null }
    }
  }

  // Load health and system metrics
  try {
    // First get basic health status
    const healthRes = await axios.get(`${API_BASE_URL}/api/health`)
    const healthData = healthRes.data
    
    // Then try to get detailed metrics if user is admin
    if (userStore.user?.role === 'admin') {
      try {
        const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
        const metricsRes = await axios.get(`${API_BASE_URL}/api/admin/system/metrics`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        if (metricsRes.data.success && metricsRes.data.data) {
          const metrics = metricsRes.data.data
          systemHealth.value = {
            apiStatus: healthData.status === 'healthy' ? 'Online' : 'Offline',
            avgResponseTime: Math.round(metrics.performance.avg_response_time || 0),
            errorRate: Math.round(metrics.performance.error_rate * 10) / 10 || 0
          }
        } else {
          // Fallback to basic health data
          systemHealth.value = {
            apiStatus: healthData.status === 'healthy' ? 'Online' : 'Offline',
            avgResponseTime: 0,
            errorRate: 0
          }
        }
      } catch (metricsError) {
        // Silently fall back to basic health data for non-critical errors
        if (metricsError.response?.status !== 404 && metricsError.response?.status !== 401) {
          console.log('Using basic health data')
        }
        // Use basic health data
        systemHealth.value = {
          apiStatus: healthData.status === 'healthy' ? 'Online' : 'Offline',
          avgResponseTime: 0,
          errorRate: 0
        }
      }
    } else {
      // Non-admin users just see basic status
      systemHealth.value = {
        apiStatus: healthData.status === 'healthy' ? 'Online' : 'Offline',
        avgResponseTime: 0,
        errorRate: 0
      }
    }
  } catch (error) {
    if (error.response?.status === 404) {
      console.log('Health endpoint not found')
    } else if (error.request) {
      console.warn('Backend server is not responding')
    } else {
      console.warn('Error checking system health:', error.message)
    }
    // If health check fails, API is likely down
    systemHealth.value = { apiStatus: 'Offline', avgResponseTime: 0, errorRate: 0 }
  }

  // Load scraping status
  try {
    // Check if any scraping is in progress
    const startupRes = await axios.get(`${API_BASE_URL}/api/startup-status`)
    if (startupRes.data) {
      // Only mark as active if we have actual scraping activity
      const isActuallyScraping = startupRes.data.scraping_in_progress || 
                                 (startupRes.data.current_class && startupRes.data.current_class !== 'None') ||
                                 (startupRes.data.progress_percent && startupRes.data.progress_percent > 0)
      
      scrapingStatus.value = {
        active: isActuallyScraping,
        currentClass: startupRes.data.current_class || null,
        progress: startupRes.data.progress_percent ? `${startupRes.data.progress_percent}%` : null
      }
    }
  } catch (error) {
    // Silently ignore - scraping status is optional
    scrapingStatus.value = {
      active: false,
      currentClass: null,
      progress: null
    }
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
      console.log('Rate limit reached for activities - will retry later')
    } else if (error.response?.status === 401 || error.response?.status === 403) {
      console.log('Activities require admin authentication')
    } else if (error.response?.status === 404) {
      console.log('Activities endpoint not found - OAuth may be disabled')
    } else if (error.response) {
      console.warn('Error loading activities:', error.response.status)
    }
    // Show empty state if no activities can be loaded
    recentActivities.value = []
  }
  
  // Activities loaded successfully

  // Load database status
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const dbRes = await axios.get(`${API_BASE_URL}/api/admin/database/config`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    if (dbRes.data.success && dbRes.data.data.database) {
      const dbData = dbRes.data.data.database
      databaseStatus.value = {
        connected: dbData.connected || false,
        host: dbData.host || null,
        database: dbData.database || null,
        status: dbData.status || 'unknown',
        version: dbData.version || null
      }
    }
  } catch (error) {
    if (error.response?.status !== 404) {
      console.warn('Could not load database status')
    }
    databaseStatus.value = {
      connected: false,
      host: null,
      database: null,
      status: 'error'
    }
  }
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

const formatConfigSource = (source) => {
  const sourceMap = {
    'persistent_storage': 'Persistent Storage',
    'environment_variable': 'Environment Variable',
    'config_json': 'Config File (Temporary)',
    'none': 'Not Configured',
    'unknown': 'Unknown'
  }
  return sourceMap[source] || source
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

// Navigate to system page
const navigateToSystem = () => {
  console.log('Navigating to system page...')
  console.log('Current user:', userStore.user)
  console.log('Is authenticated:', userStore.isAuthenticated)
  console.log('Is admin:', userStore.user?.role === 'admin')
  
  // Force navigation to system page
  router.push('/admin/system').catch(err => {
    console.error('Navigation error:', err)
  })
}

// Database configuration methods
const updateDefaultPort = () => {
  switch (databaseForm.value.db_type) {
    case 'mssql':
      databaseForm.value.port = 1433
      break
    case 'mysql':
      databaseForm.value.port = 3306
      break
    case 'postgresql':
      databaseForm.value.port = 5432
      break
  }
}

const openDatabaseModal = async () => {
  // Try to load stored configuration even if database is disconnected
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const configRes = await axios.get(`${API_BASE_URL}/api/admin/database/stored-config`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    if (configRes.data.success && configRes.data.data) {
      const config = configRes.data.data
      databaseForm.value = {
        db_type: config.database_type || 'mysql',
        host: config.host || '',
        port: config.port || (config.database_type === 'mysql' ? 3306 : config.database_type === 'mssql' ? 1433 : 5432),
        database: config.database_name || '',
        username: config.username || '',
        password: '', // Password is not returned for security
        use_ssl: config.database_ssl !== undefined ? config.database_ssl : true
      }
    } else {
      // Fallback to current status if stored config not available
      if (databaseStatus.value.db_type) {
        databaseForm.value = {
          db_type: databaseStatus.value.db_type || 'mysql',
          host: databaseStatus.value.host || '',
          port: databaseStatus.value.port || (databaseStatus.value.db_type === 'mysql' ? 3306 : databaseStatus.value.db_type === 'mssql' ? 1433 : 5432),
          database: databaseStatus.value.database || '',
          username: databaseStatus.value.username || '',
          password: '', // Password is not returned for security
          use_ssl: databaseStatus.value.use_ssl !== undefined ? databaseStatus.value.use_ssl : true
        }
      }
    }
  } catch (error) {
    console.log('Could not load stored configuration, using defaults')
  }
  
  showDatabaseModal.value = true
}

const closeDatabaseModal = () => {
  showDatabaseModal.value = false
  databaseTestResult.value = null
  // Reset form
  databaseForm.value = {
    db_type: 'mssql',
    host: '',
    port: 1433,
    database: '',
    username: '',
    password: '',
    use_ssl: true
  }
}

const testDatabaseConnection = async () => {
  testingConnection.value = true
  databaseTestResult.value = null
  
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const response = await axios.post(`${API_BASE_URL}/api/admin/database/test`, {
      db_type: databaseForm.value.db_type,
      host: databaseForm.value.host,
      port: databaseForm.value.port,
      database: databaseForm.value.database,
      username: databaseForm.value.username,
      password: databaseForm.value.password,
      use_ssl: databaseForm.value.use_ssl
    }, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    if (response.data.success) {
      databaseTestResult.value = {
        success: true,
        message: `Connection successful! Database version: ${response.data.data.database_version.split(' ')[0]} (${response.data.data.connection_time_ms}ms)`,
        data: response.data.data
      }
    } else {
      databaseTestResult.value = {
        success: false,
        message: response.data.message || 'Connection test failed',
        error: response.data.error
      }
    }
  } catch (error) {
    console.error('Database test error:', error)
    const errorData = error.response?.data
    databaseTestResult.value = {
      success: false,
      message: errorData?.message || 'Connection test failed',
      error: errorData?.error || {
        error_type: 'network_error',
        error_message: error.message,
        details: {
          issue: 'Unable to reach server',
          suggestion: 'Check that the backend server is running and accessible'
        }
      }
    }
  } finally {
    testingConnection.value = false
  }
}

const refreshConnection = async () => {
  refreshingConnection.value = true
  connectionTestResult.value = null
  
  try {
    // First, try to refresh the database configuration
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const dbConfigRes = await axios.get(`${API_BASE_URL}/api/admin/database/config`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    if (dbConfigRes.data.success && dbConfigRes.data.data?.database) {
      const dbData = dbConfigRes.data.data.database
      
      // Update the database status
      databaseStatus.value = {
        connected: dbData.connected || false,
        host: dbData.host || null,
        port: dbData.port || null,
        database: dbData.database || null,
        username: dbData.username || null,
        db_type: dbData.db_type || null,
        use_ssl: dbData.use_ssl !== undefined ? dbData.use_ssl : true,
        status: dbData.status || 'unknown',
        version: dbData.version || null,
        connection_type: dbData.connection_type || 'unknown'
      }
      
      // Update storage info if available
      if (dbConfigRes.data.data.storage_info) {
        storageInfo.value = dbConfigRes.data.data.storage_info
      }
      
      // Force backend to reconnect by invalidating cache
      try {
        await axios.post(`${API_BASE_URL}/api/admin/database/reconnect`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        })
      } catch (e) {
        // Endpoint might not exist yet, that's ok
        console.log('Reconnect endpoint not available, connection will refresh on next use')
      }
      
      // Show success message
      if (databaseStatus.value.connected) {
        alert('Database connection refreshed successfully!')
      } else {
        alert('Database configuration loaded but connection failed. Please check your settings.')
      }
    }
  } catch (error) {
    console.error('Failed to refresh connection:', error)
    
    // Provide more specific error messages
    let errorMessage = 'Failed to refresh database connection.'
    
    if (error.response) {
      // Server responded with an error
      if (error.response.status === 503) {
        errorMessage = 'Database service unavailable. The backend server may be unable to connect to the database.'
      } else if (error.response.data?.message) {
        errorMessage = error.response.data.message
      } else {
        errorMessage = `Server error: ${error.response.status}`
      }
    } else if (error.request) {
      // Request was made but no response
      errorMessage = 'Unable to reach the backend server. Please check your connection.'
    } else {
      // Something else happened
      errorMessage = error.message || 'An unexpected error occurred'
    }
    
    alert(errorMessage + '\n\nCheck the browser console for more details.')
  } finally {
    refreshingConnection.value = false
  }
}

const runDiagnostics = async () => {
  runningDiagnostics.value = true
  
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const response = await axios.get(`${API_BASE_URL}/api/admin/database/diagnostics`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    if (response.data.success && response.data.data) {
      const diag = response.data.data
      
      // Build diagnostic report
      let report = 'Database Diagnostics Report\n' + '='.repeat(40) + '\n\n'
      
      // Environment
      report += 'Environment:\n'
      for (const [key, value] of Object.entries(diag.environment || {})) {
        report += `  ${key}: ${value}\n`
      }
      
      // Config checks
      report += '\nConfiguration:\n'
      if (diag.config_checks) {
        report += `  Config found: ${diag.config_checks.persistent_config_found ? 'Yes' : 'No'}\n`
        if (diag.config_checks.persistent_config_found) {
          report += `  Source: ${diag.config_checks.config_source}\n`
          report += `  Host: ${diag.config_checks.host || 'N/A'}\n`
          report += `  Port: ${diag.config_checks.port || 'N/A'}\n`
          report += `  Database: ${diag.config_checks.database || 'N/A'}\n`
          report += `  Username: ${diag.config_checks.username || 'N/A'}\n`
          report += `  Has password: ${diag.config_checks.has_password ? 'Yes' : 'No'}\n`
        }
        if (diag.config_checks.error) {
          report += `  Error: ${diag.config_checks.error}\n`
        }
      }
      
      // Connection test
      report += '\nConnection Test:\n'
      if (diag.connection_test) {
        report += `  Success: ${diag.connection_test.success ? 'Yes' : 'No'}\n`
        if (diag.connection_test.success) {
          report += `  Database type: ${diag.connection_test.db_type}\n`
          report += `  Query test: ${diag.connection_test.query_test}\n`
        } else {
          report += `  Error: ${diag.connection_test.error || 'Unknown'}\n`
        }
      }
      
      // Persistent storage
      report += '\nPersistent Storage:\n'
      if (diag.persistent_storage) {
        report += `  Data directory: ${diag.persistent_storage.data_directory || 'N/A'}\n`
        report += `  Directory exists: ${diag.persistent_storage.directory_exists ? 'Yes' : 'No'}\n`
        report += `  Directory writable: ${diag.persistent_storage.directory_writable ? 'Yes' : 'No'}\n`
        report += `  Config file exists: ${diag.persistent_storage.config_file_exists ? 'Yes' : 'No'}\n`
      }
      
      // Recommendations
      if (diag.recommendations && diag.recommendations.length > 0) {
        report += '\nRecommendations:\n'
        for (const rec of diag.recommendations) {
          report += `  • ${rec}\n`
        }
      }
      
      // Show report
      console.log(report)
      alert(report)
    } else {
      alert('Failed to run diagnostics. Check console for details.')
    }
  } catch (error) {
    console.error('Diagnostics error:', error)
    
    let errorMessage = 'Failed to run diagnostics: '
    if (error.response?.data?.message) {
      errorMessage += error.response.data.message
    } else if (error.message) {
      errorMessage += error.message
    } else {
      errorMessage += 'Unknown error'
    }
    
    alert(errorMessage)
  } finally {
    runningDiagnostics.value = false
  }
}

const saveDatabaseConfig = async () => {
  if (!databaseTestResult.value?.success) {
    alert('Please test the connection first before saving')
    return
  }
  
  savingConfig.value = true
  
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const response = await axios.post(`${API_BASE_URL}/api/admin/database/config`, {
      db_type: databaseForm.value.db_type,
      host: databaseForm.value.host,
      port: databaseForm.value.port,
      database: databaseForm.value.database,
      username: databaseForm.value.username,
      password: databaseForm.value.password,
      use_ssl: databaseForm.value.use_ssl
    }, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    if (response.data.success) {
      // Update database status with all fields
      const dbData = response.data.data.database
      databaseStatus.value = {
        connected: true,
        host: dbData.host,
        port: dbData.port,
        database: dbData.database,
        username: dbData.username,
        db_type: dbData.db_type,
        use_ssl: dbData.use_ssl,
        status: 'connected',
        version: dbData.version,
        connection_type: 'config'
      }
      
      // Close modal
      closeDatabaseModal()
      
      // Show success message
      alert('Database configuration saved successfully!')
      
      // Refresh dashboard data
      await loadDashboardData()
    } else {
      alert('Failed to save database configuration: ' + (response.data.message || 'Unknown error'))
    }
  } catch (error) {
    console.error('Save database config error:', error)
    alert('Failed to save database configuration: ' + (error.response?.data?.message || 'Unknown error'))
  } finally {
    savingConfig.value = false
  }
}

// Remove mock data generation - we'll use real data from the API

// Diagnostics modal functions
const openDiagnosticsModal = () => {
  showDiagnosticsModal.value = true
  diagnosticsResult.value = null
  connectionTestResult.value = null
}

const closeDiagnosticsModal = () => {
  showDiagnosticsModal.value = false
}

const openNetworkTest = () => {
  closeDiagnosticsModal()
  setTimeout(() => {
    openNetworkTestModal()
  }, 300)
}

// Network test functions
const openNetworkTestModal = () => {
  showNetworkTestModal.value = true
  networkTestResult.value = null
}

const closeNetworkTestModal = () => {
  showNetworkTestModal.value = false
  networkTestResult.value = null
}

const setQuickTest = (host, port, type) => {
  networkTestForm.value.host = host
  networkTestForm.value.port = port
  networkTestForm.value.test_type = type
}

const formatTestName = (name) => {
  return name.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}

const runNetworkTest = async () => {
  testingNetwork.value = true
  networkTestResult.value = null
  
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const response = await axios.post(`${API_BASE_URL}/api/admin/network/test`, {
      host: networkTestForm.value.host,
      port: networkTestForm.value.port,
      test_type: networkTestForm.value.test_type,
      username: networkTestForm.value.username,
      password: networkTestForm.value.password,
      database: networkTestForm.value.database
    }, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    if (response.data.success) {
      networkTestResult.value = response.data.data
    } else {
      console.error('Network test failed:', response.data.message)
    }
  } catch (error) {
    console.error('Network test error:', error)
    networkTestResult.value = {
      host: networkTestForm.value.host,
      port: networkTestForm.value.port,
      overall_success: false,
      tests: {
        api_error: {
          success: false,
          error: error.message,
          message: 'Failed to run network test'
        }
      }
    }
  } finally {
    testingNetwork.value = false
  }
}

// Lifecycle
onMounted(async () => {
  // Load dashboard data on mount
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

.card-icon.database {
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
}

.card-icon.database.status-connected {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
}

.card-icon.database.status-disconnected {
  background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
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

.stat-row.warning-row {
  background: rgba(251, 191, 36, 0.1);
  padding: 12px;
  margin: 8px -20px -20px;
  border-radius: 0 0 8px 8px;
  border: none;
  gap: 10px;
}

.warning-text {
  color: #fbbf24;
  font-size: 0.9rem;
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

.stat-value.info {
  color: #60a5fa;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

.card-actions {
  text-align: center;
}

.card-actions.database-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
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
  border: none;
  cursor: pointer;
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

/* Database Configuration Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(45, 55, 72, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  border: 1px solid rgba(255, 255, 255, 0.1);
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30px 30px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f7fafc;
  margin: 0;
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.modal-close {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 5px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.modal-close:hover {
  color: #f7fafc;
  background: rgba(255, 255, 255, 0.1);
}

.modal-body {
  padding: 30px;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #f7fafc;
  font-size: 0.95rem;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  color: #f7fafc;
  font-size: 1rem;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2);
  background: rgba(0, 0, 0, 0.4);
}

.form-input::placeholder {
  color: #9ca3af;
}

.checkbox-group {
  display: flex;
  align-items: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  margin-bottom: 0;
}

.form-checkbox {
  margin-right: 12px;
  width: 18px;
  height: 18px;
  accent-color: #8b5cf6;
}

.checkbox-text {
  color: #f7fafc;
  font-weight: 500;
}

.test-result {
  margin-top: 20px;
  padding: 16px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 500;
}

.test-result.success {
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #4ade80;
}

.test-result.error {
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
}

.test-details {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 0.9rem;
}

.test-details p {
  margin: 6px 0;
  opacity: 0.9;
}

.error-details {
  margin-top: 15px;
  padding: 15px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(255, 107, 107, 0.2);
}

.error-issue {
  margin-bottom: 10px;
  font-size: 0.95em;
  color: #ff6b6b;
}

.error-suggestion {
  margin-bottom: 10px;
  font-size: 0.9em;
  color: rgba(255, 255, 255, 0.8);
}

.error-technical {
  margin-top: 10px;
  font-size: 0.85em;
}

.error-technical summary {
  cursor: pointer;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 5px;
}

.error-technical summary:hover {
  color: rgba(255, 255, 255, 0.8);
}

.error-technical code {
  display: block;
  margin-top: 5px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85em;
  color: rgba(255, 255, 255, 0.7);
  word-wrap: break-word;
  white-space: pre-wrap;
}

.modal-footer {
  display: flex;
  gap: 16px;
  padding: 20px 30px 30px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.test-button, .save-button, .cancel-button {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.test-button {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  flex: 1;
}

.test-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
}

.save-button {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  flex: 1;
}

.save-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3);
}

.cancel-button {
  background: rgba(0, 0, 0, 0.3);
  color: #9ca3af;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.cancel-button:hover {
  background: rgba(0, 0, 0, 0.5);
  color: #f7fafc;
  border-color: rgba(255, 255, 255, 0.2);
}

.test-button:disabled, .save-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
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
  
  .modal-content {
    margin: 10px;
    max-width: none;
  }
  
  .modal-header, .modal-body, .modal-footer {
    padding: 20px;
  }
  
  .modal-footer {
    flex-direction: column;
  }
}
</style>

/* Network Test Modal Styles */
.quick-tests {
  margin: 20px 0;
  padding: 15px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.quick-tests p {
  margin: 0 0 10px 0;
  font-weight: bold;
  color: var(--primary);
}

.quick-test-btn {
  margin: 5px;
  padding: 8px 16px;
  background: rgba(138, 43, 226, 0.2);
  border: 1px solid var(--primary);
  border-radius: 4px;
  color: var(--text);
  cursor: pointer;
  transition: all 0.3s ease;
}

.quick-test-btn:hover {
  background: rgba(138, 43, 226, 0.3);
  transform: translateY(-1px);
}

.test-results {
  margin-top: 20px;
  padding: 20px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
}

.test-results.success {
  border: 1px solid #4caf50;
}

.test-results.error {
  border: 1px solid #f44336;
}

.test-results h3 {
  margin: 0 0 15px 0;
  color: var(--primary);
}

.test-item {
  margin: 10px 0;
  padding: 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.test-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

.test-header .fa-check-circle {
  color: #4caf50;
}

.test-header .fa-times-circle {
  color: #f44336;
}

.test-time {
  margin-left: auto;
  font-size: 0.9em;
  color: #888;
}

.test-message {
  margin: 5px 0;
  font-size: 0.95em;
}

.test-error {
  margin: 5px 0;
  color: #ff6b6b;
  font-size: 0.9em;
}

.test-detail {
  margin: 5px 0;
  color: #888;
  font-size: 0.9em;
  font-family: monospace;
}


/* Diagnostics Modal Styles */
.diagnostics-modal {
  max-width: 700px;
}

.diagnostic-tests {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  margin: 20px 0;
}

.test-card {
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(138, 43, 226, 0.3);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.test-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--primary);
  transform: translateY(-2px);
}

.test-card .test-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.test-card .test-header i {
  font-size: 24px;
  color: var(--primary);
}

.test-card h3 {
  margin: 0;
  color: var(--primary);
  font-size: 1.2em;
}

.test-card p {
  margin: 10px 0 15px 0;
  color: #ccc;
  line-height: 1.5;
}

.test-button {
  padding: 10px 20px;
  background: rgba(138, 43, 226, 0.2);
  border: 1px solid var(--primary);
  border-radius: 4px;
  color: var(--text);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.test-button:hover {
  background: rgba(138, 43, 226, 0.3);
  transform: translateY(-1px);
}

.test-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.diagnostics-result {
  margin-top: 30px;
  padding: 20px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.diagnostics-result h3 {
  margin: 0 0 15px 0;
  color: var(--primary);
}

.result-content {
  background: rgba(0, 0, 0, 0.5);
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
}

.result-content pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
  color: #ddd;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.connection-result {
  margin-top: 20px;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid;
}

.connection-result.success {
  background: rgba(76, 175, 80, 0.1);
  border-color: #4caf50;
}

.connection-result.error {
  background: rgba(244, 67, 54, 0.1);
  border-color: #f44336;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.result-header i {
  font-size: 20px;
}

.result-header .fa-check-circle {
  color: #4caf50;
}

.result-header .fa-times-circle {
  color: #f44336;
}

.result-details {
  color: #ccc;
  font-size: 0.95em;
  line-height: 1.5;
}

/* Update database actions to prevent cramping */
.database-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.database-actions .action-button {
  flex: 1;
  min-width: 120px;
}
