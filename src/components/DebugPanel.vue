<template>
  <div v-if="showDebugPanel" class="debug-panel">
    <div class="debug-header">
      <h3>🔧 Debug Panel</h3>
      <button @click="togglePanel" class="toggle-btn">{{ expanded ? '−' : '+' }}</button>
      <button @click="closePanel" class="close-btn">×</button>
    </div>
    
    <div v-if="expanded" class="debug-content">
      <!-- Environment Info -->
      <div class="debug-section">
        <h4>🌍 Environment</h4>
        <div class="debug-item">
          <span class="label">Mode:</span>
          <span class="value" :class="isProd ? 'prod' : 'dev'">{{ isProd ? 'Production' : 'Development' }}</span>
        </div>
        <div class="debug-item">
          <span class="label">API Base URL:</span>
          <span class="value">{{ apiBaseUrl }}</span>
        </div>
        <div class="debug-item">
          <span class="label">VITE_BACKEND_URL:</span>
          <span class="value">{{ viteBackendUrl || 'Not set' }}</span>
        </div>
        <div class="debug-item">
          <span class="label">Timestamp:</span>
          <span class="value">{{ new Date().toISOString() }}</span>
        </div>
      </div>

      <!-- Connection Status -->
      <div class="debug-section">
        <h4>🔗 Connection Status</h4>
        <div class="debug-item">
          <span class="label">Backend Health:</span>
          <span class="value" :class="healthStatus.status">
            {{ healthStatus.message }}
            <button @click="testHealth" class="test-btn" :disabled="healthStatus.testing">
              {{ healthStatus.testing ? '...' : 'Test' }}
            </button>
          </span>
        </div>
        <div class="debug-item">
          <span class="label">Cache Status:</span>
          <span class="value" :class="cacheStatus.status">
            {{ cacheStatus.message }}
            <button @click="testCache" class="test-btn" :disabled="cacheStatus.testing">
              {{ cacheStatus.testing ? '...' : 'Test' }}
            </button>
          </span>
        </div>
        <div class="debug-item">
          <span class="label">Sample API Call:</span>
          <span class="value" :class="sampleApiStatus.status">
            {{ sampleApiStatus.message }}
            <button @click="testSampleApi" class="test-btn" :disabled="sampleApiStatus.testing">
              {{ sampleApiStatus.testing ? '...' : 'Test' }}
            </button>
          </span>
        </div>
      </div>

      <!-- Recent Network Activity -->
      <div class="debug-section">
        <h4>📡 Recent Network Activity</h4>
        <div class="network-log">
          <div v-if="networkLog.length === 0" class="no-activity">
            No recent network activity
          </div>
          <div v-for="(entry, index) in networkLog.slice(-5)" :key="index" class="network-entry" :class="entry.type">
            <div class="network-time">{{ formatTime(entry.timestamp) }}</div>
            <div class="network-method">{{ entry.method }}</div>
            <div class="network-url">{{ entry.url.replace(apiBaseUrl, '') }}</div>
            <div class="network-status" :class="entry.success ? 'success' : 'error'">
              {{ entry.success ? entry.status : 'FAILED' }}
            </div>
            <div class="network-duration">{{ entry.duration }}ms</div>
          </div>
        </div>
        <button @click="clearNetworkLog" class="clear-btn">Clear Log</button>
      </div>

      <!-- Debug Actions -->
      <div class="debug-section">
        <h4>🛠️ Debug Actions</h4>
        <div class="debug-actions">
          <button @click="enableNetworkDebug" class="action-btn">Enable Network Debug</button>
          <button @click="runFullTest" class="action-btn" :disabled="runningFullTest">
            {{ runningFullTest ? 'Running...' : 'Run Full Test' }}
          </button>
          <button @click="exportDebugInfo" class="action-btn">Export Debug Info</button>
          <button @click="clearAllData" class="action-btn danger">Clear All Data</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useSpellsStore } from '../stores/spells'
import axios from 'axios'

export default {
  name: 'DebugPanel',
  data() {
    return {
      showDebugPanel: false,
      expanded: true,
      healthStatus: { status: 'unknown', message: 'Not tested', testing: false },
      cacheStatus: { status: 'unknown', message: 'Not tested', testing: false },
      sampleApiStatus: { status: 'unknown', message: 'Not tested', testing: false },
      networkLog: [],
      runningFullTest: false
    }
  },
  setup() {
    const spellsStore = useSpellsStore()
    return { spellsStore }
  },
  computed: {
    isProd() {
      return import.meta.env.PROD
    },
    viteBackendUrl() {
      return import.meta.env.VITE_BACKEND_URL
    },
    apiBaseUrl() {
      // Mirror the logic from spells.js
      if (import.meta.env.PROD) {
        const envUrl = import.meta.env.VITE_BACKEND_URL
        if (envUrl && !envUrl.includes('localhost') && !envUrl.includes('127.0.0.1')) {
          return envUrl
        }
        return 'https://eqdatascraper-backend-production.up.railway.app'
      }
      return import.meta.env.VITE_BACKEND_URL || 'http://localhost:5001'
    }
  },
  mounted() {
    // Only show debug panel when explicitly enabled via localStorage
    this.showDebugPanel = localStorage.getItem('debug-panel') === 'true'
    
    // Listen for network activity from the stores
    this.setupNetworkLogging()
    
    // Auto-run tests on mount only if debug panel is showing
    if (this.showDebugPanel) {
      this.$nextTick(() => {
        this.runFullTest()
      })
    }
  },
  methods: {
    togglePanel() {
      this.expanded = !this.expanded
    },
    
    closePanel() {
      this.showDebugPanel = false
      localStorage.setItem('debug-panel', 'false')
    },
    
    toggleDebugPanel() {
      this.showDebugPanel = !this.showDebugPanel
      localStorage.setItem('debug-panel', this.showDebugPanel ? 'true' : 'false')
      
      // Auto-run tests when opening
      if (this.showDebugPanel) {
        this.$nextTick(() => {
          this.runFullTest()
        })
      }
    },
    
    setupNetworkLogging() {
      // Override axios to capture network activity
      const originalAxios = axios.get
      const self = this
      
      axios.get = async function(...args) {
        const url = args[0]
        const startTime = Date.now()
        
        try {
          const response = await originalAxios.apply(this, args)
          const duration = Date.now() - startTime
          
          self.logNetworkActivity({
            method: 'GET',
            url,
            status: response.status,
            success: true,
            duration,
            timestamp: Date.now()
          })
          
          return response
        } catch (error) {
          const duration = Date.now() - startTime
          
          self.logNetworkActivity({
            method: 'GET',
            url,
            status: error.response?.status || 'ERR',
            success: false,
            duration,
            timestamp: Date.now(),
            error: error.message
          })
          
          throw error
        }
      }
    },
    
    logNetworkActivity(entry) {
      this.networkLog.push(entry)
      
      // Keep only last 20 entries
      if (this.networkLog.length > 20) {
        this.networkLog = this.networkLog.slice(-20)
      }
    },
    
    async testHealth() {
      this.healthStatus.testing = true
      try {
        const response = await axios.get(`${this.apiBaseUrl}/api/health`, { timeout: 10000 })
        this.healthStatus = {
          status: 'success',
          message: `OK (${response.status})`,
          testing: false
        }
      } catch (error) {
        this.healthStatus = {
          status: 'error',
          message: `Failed: ${error.message}`,
          testing: false
        }
      }
    },
    
    async testCache() {
      this.cacheStatus.testing = true
      try {
        const response = await axios.get(`${this.apiBaseUrl}/api/cache-status`, { timeout: 10000 })
        const cacheKeys = Object.keys(response.data).filter(key => key !== '_config')
        this.cacheStatus = {
          status: 'success',
          message: `OK (${cacheKeys.length} cached classes)`,
          testing: false
        }
      } catch (error) {
        this.cacheStatus = {
          status: 'error',
          message: `Failed: ${error.message}`,
          testing: false
        }
      }
    },
    
    async testSampleApi() {
      this.sampleApiStatus.testing = true
      try {
        const response = await axios.get(`${this.apiBaseUrl}/api/spells/warrior`, { timeout: 15000 })
        const spellCount = response.data.spells?.length || response.data.length || 0
        this.sampleApiStatus = {
          status: 'success',
          message: `OK (${spellCount} spells)`,
          testing: false
        }
      } catch (error) {
        this.sampleApiStatus = {
          status: 'error',
          message: `Failed: ${error.message}`,
          testing: false
        }
      }
    },
    
    async runFullTest() {
      this.runningFullTest = true
      console.log('🔧 Running full debug test suite...')
      
      await this.testHealth()
      await new Promise(resolve => setTimeout(resolve, 500))
      
      await this.testCache()
      await new Promise(resolve => setTimeout(resolve, 500))
      
      await this.testSampleApi()
      
      this.runningFullTest = false
      console.log('🔧 Debug test suite completed')
    },
    
    enableNetworkDebug() {
      localStorage.setItem('debug-network', 'true')
      alert('Network debugging enabled. Check console for detailed logs.')
    },
    
    exportDebugInfo() {
      const debugInfo = {
        environment: {
          isProd: this.isProd,
          apiBaseUrl: this.apiBaseUrl,
          viteBackendUrl: this.viteBackendUrl,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString()
        },
        connectionStatus: {
          health: this.healthStatus,
          cache: this.cacheStatus,
          sampleApi: this.sampleApiStatus
        },
        networkLog: this.networkLog,
        localStorage: {
          debugNetwork: localStorage.getItem('debug-network'),
          debugPanel: localStorage.getItem('debug-panel')
        }
      }
      
      const blob = new Blob([JSON.stringify(debugInfo, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `debug-info-${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
    },
    
    clearAllData() {
      if (confirm('Clear all debug data and refresh the page?')) {
        localStorage.clear()
        this.networkLog = []
        location.reload()
      }
    },
    
    clearNetworkLog() {
      this.networkLog = []
    },
    
    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString()
    }
  }
}
</script>

<style scoped>
.debug-panel {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 400px;
  max-height: 80vh;
  background: linear-gradient(145deg, rgba(0, 0, 0, 0.95), rgba(20, 20, 30, 0.95));
  backdrop-filter: blur(15px);
  border: 2px solid rgba(147, 112, 219, 0.3);
  border-radius: 12px;
  color: white;
  font-family: 'JetBrains Mono', 'Monaco', monospace;
  font-size: 12px;
  z-index: 10000;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.debug-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: rgba(147, 112, 219, 0.2);
  border-bottom: 1px solid rgba(147, 112, 219, 0.3);
}

.debug-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.toggle-btn, .close-btn {
  background: none;
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  width: 25px;
  height: 25px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toggle-btn:hover, .close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.debug-content {
  max-height: 70vh;
  overflow-y: auto;
  padding: 15px;
}

.debug-section {
  margin-bottom: 15px;
}

.debug-section h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: rgba(147, 112, 219, 1);
  border-bottom: 1px solid rgba(147, 112, 219, 0.3);
  padding-bottom: 4px;
}

.debug-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.label {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  font-size: 11px;
}

.value {
  color: rgba(255, 255, 255, 0.9);
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.value.prod {
  color: #ff6b6b;
  font-weight: bold;
}

.value.dev {
  color: #51cf66;
  font-weight: bold;
}

.value.success {
  color: #51cf66;
}

.value.error {
  color: #ff6b6b;
}

.value.unknown {
  color: #ffd43b;
}

.test-btn {
  background: rgba(147, 112, 219, 0.3);
  border: 1px solid rgba(147, 112, 219, 0.5);
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 10px;
}

.test-btn:hover:not(:disabled) {
  background: rgba(147, 112, 219, 0.5);
}

.test-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.network-log {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
  padding: 8px;
  max-height: 150px;
  overflow-y: auto;
  margin-bottom: 8px;
}

.no-activity {
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
  padding: 10px;
  font-style: italic;
}

.network-entry {
  display: grid;
  grid-template-columns: auto auto 1fr auto auto;
  gap: 8px;
  padding: 4px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 10px;
  align-items: center;
}

.network-entry:last-child {
  border-bottom: none;
}

.network-time {
  color: rgba(255, 255, 255, 0.6);
}

.network-method {
  color: #74c0fc;
  font-weight: bold;
}

.network-url {
  color: rgba(255, 255, 255, 0.8);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.network-status.success {
  color: #51cf66;
}

.network-status.error {
  color: #ff6b6b;
}

.network-duration {
  color: rgba(255, 255, 255, 0.6);
}

.debug-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.action-btn {
  background: rgba(147, 112, 219, 0.2);
  border: 1px solid rgba(147, 112, 219, 0.4);
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  transition: all 0.2s ease;
}

.action-btn:hover:not(:disabled) {
  background: rgba(147, 112, 219, 0.4);
  border-color: rgba(147, 112, 219, 0.6);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.danger {
  background: rgba(255, 107, 107, 0.2);
  border-color: rgba(255, 107, 107, 0.4);
}

.action-btn.danger:hover:not(:disabled) {
  background: rgba(255, 107, 107, 0.4);
  border-color: rgba(255, 107, 107, 0.6);
}

.clear-btn {
  background: rgba(108, 117, 125, 0.3);
  border: 1px solid rgba(108, 117, 125, 0.5);
  color: white;
  padding: 4px 8px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 10px;
}

.clear-btn:hover {
  background: rgba(108, 117, 125, 0.5);
}

/* Scrollbar styling */
.debug-content::-webkit-scrollbar,
.network-log::-webkit-scrollbar {
  width: 6px;
}

.debug-content::-webkit-scrollbar-track,
.network-log::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.debug-content::-webkit-scrollbar-thumb,
.network-log::-webkit-scrollbar-thumb {
  background: rgba(147, 112, 219, 0.5);
  border-radius: 3px;
}

.debug-content::-webkit-scrollbar-thumb:hover,
.network-log::-webkit-scrollbar-thumb:hover {
  background: rgba(147, 112, 219, 0.7);
}

@media (max-width: 768px) {
  .debug-panel {
    width: 90vw;
    max-width: 350px;
    bottom: 10px;
    right: 10px;
  }
  
  .debug-actions {
    grid-template-columns: 1fr;
  }
}</style>