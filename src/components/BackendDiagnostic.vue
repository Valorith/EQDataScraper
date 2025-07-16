<template>
  <div class="backend-diagnostic">
    <h3>Backend Connection Diagnostic</h3>
    
    <div class="diagnostic-section">
      <h4>Current Configuration</h4>
      <div class="config-info">
        <div class="config-item">
          <span class="label">Environment Config:</span>
          <span class="value">{{ expectedBackendUrl }}</span>
        </div>
        <div class="config-item">
          <span class="label">Current URL:</span>
          <span class="value">{{ currentBackendUrl || 'Not configured' }}</span>
        </div>
        <div v-if="portMismatch" class="config-item mismatch-warning">
          <span class="label">⚠️ Warning:</span>
          <span class="value warning">{{ portMismatch.message }}</span>
        </div>
        <div class="config-item">
          <span class="label">Status:</span>
          <span class="status" :class="connectionStatus.class">{{ connectionStatus.text }}</span>
        </div>
      </div>
    </div>

    <div class="diagnostic-section">
      <h4>Browser Information</h4>
      <div class="browser-info">
        <div class="info-item">
          <span class="label">User Agent:</span>
          <span class="value small">{{ browserInfo.userAgent }}</span>
        </div>
        <div class="info-item">
          <span class="label">Online Status:</span>
          <span class="value" :class="{ 'status-success': browserInfo.online, 'status-error': !browserInfo.online }">
            {{ browserInfo.online ? 'Online' : 'Offline' }}
          </span>
        </div>
        <div class="info-item">
          <span class="label">Current Origin:</span>
          <span class="value">{{ browserInfo.origin }}</span>
        </div>
        <div class="info-item">
          <span class="label">Protocol:</span>
          <span class="value">{{ browserInfo.protocol }}</span>
        </div>
      </div>
    </div>

    <div class="diagnostic-section">
      <h4>Test Results</h4>
      <div class="test-results">
        <div v-for="test in testResults" :key="test.url" class="test-item">
          <div>
            <div class="test-url">{{ test.url }}</div>
            <div class="test-status" :class="test.statusClass">
              <span v-if="test.loading" class="loading-spinner">⟳</span>
              <span v-else>{{ test.status }}</span>
            </div>
            <button 
              v-if="test.success && test.url !== currentBackendUrl" 
              @click="useBackend(test.url)"
              class="use-button"
            >
              Use This
            </button>
          </div>
          <div v-if="test.details" class="test-details">
            {{ test.details }}
          </div>
        </div>
      </div>
    </div>

    <div class="diagnostic-section">
      <h4>Common Port Options</h4>
      <div class="port-options">
        <button 
          v-for="port in commonPorts" 
          :key="port"
          @click="testPort(port)"
          class="port-button"
          :class="{ active: isPortActive(port) }"
        >
          Test Port {{ port }}
        </button>
      </div>
    </div>

    <div class="diagnostic-section">
      <h4>Manual Configuration</h4>
      <div class="manual-config">
        <input 
          v-model="customUrl" 
          placeholder="Enter custom backend URL (e.g., http://localhost:5001)"
          @keyup.enter="testCustomUrl"
        />
        <button @click="testCustomUrl" class="test-custom-button">Test Custom URL</button>
      </div>
    </div>

    <div class="diagnostic-actions">
      <button @click="runFullDiagnostic" class="primary-button">Run Full Diagnostic</button>
      <button @click="testAllEndpoints" class="secondary-button">Test All Endpoints</button>
      <button @click="exportReport" class="secondary-button">Export Report</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useBackendStatus } from '@/composables/useBackendStatus'
import axios from 'axios'

const emit = defineEmits(['close', 'backendChanged'])

const { backendUrl, isConnected, checkBackendStatus } = useBackendStatus()

// Dynamically determine expected backend URL from environment
const expectedBackendUrl = computed(() => {
  // First check VITE_BACKEND_URL environment variable
  const envUrl = import.meta.env.VITE_BACKEND_URL
  if (envUrl) return envUrl
  
  // Fall back to production default if in production mode
  if (import.meta.env.PROD) {
    return 'https://eqdatascraper-backend-production.up.railway.app'
  }
  
  // Default to localhost:5001 for development
  return 'http://localhost:5001'
})

const expectedPort = computed(() => {
  try {
    const url = new URL(expectedBackendUrl.value)
    return url.port || (url.protocol === 'https:' ? '443' : '80')
  } catch {
    return '5001'
  }
})

const currentBackendUrl = computed(() => backendUrl.value)
const testResults = ref([])
const commonPorts = ref([5000, 5001, 5002, 8000, 8080, 3001])
const customUrl = ref('')

// Check for port mismatches
const portMismatch = computed(() => {
  if (!currentBackendUrl.value || !expectedBackendUrl.value) return null
  
  try {
    const current = new URL(currentBackendUrl.value)
    const expected = new URL(expectedBackendUrl.value)
    
    if (current.host !== expected.host) {
      return {
        type: 'host',
        current: current.host,
        expected: expected.host,
        message: `Backend URL mismatch detected. Expected ${expected.host} but using ${current.host}`
      }
    }
  } catch {
    return null
  }
  
  return null
})

const browserInfo = computed(() => ({
  userAgent: navigator.userAgent,
  online: navigator.onLine,
  origin: window.location.origin,
  protocol: window.location.protocol
}))

const connectionStatus = computed(() => {
  if (isConnected.value) {
    return { text: 'Connected', class: 'status-connected' }
  }
  return { text: 'Disconnected', class: 'status-disconnected' }
})

const isPortActive = (port) => {
  return currentBackendUrl.value.includes(`:${port}`)
}

const testBackendUrl = async (url) => {
  const testResult = {
    url,
    loading: true,
    success: false,
    status: 'Testing...',
    statusClass: 'status-testing',
    details: null,
    responseTime: null,
    timestamp: new Date().toISOString()
  }
  
  // Add or update test result
  const existingIndex = testResults.value.findIndex(t => t.url === url)
  if (existingIndex >= 0) {
    testResults.value[existingIndex] = testResult
  } else {
    testResults.value.push(testResult)
  }
  
  const startTime = performance.now()
  
  try {
    const response = await axios.get(`${url}/api/health`, { 
      timeout: 10000,  // Increased timeout to 10 seconds
      validateStatus: () => true,
      headers: {
        'Accept': 'application/json'
      }
    })
    
    const endTime = performance.now()
    testResult.responseTime = Math.round(endTime - startTime)
    testResult.loading = false
    
    if (response.status === 200) {
      testResult.success = true
      testResult.status = `✓ Connected (${testResult.responseTime}ms)`
      testResult.statusClass = 'status-success'
      testResult.details = response.data?.status || 'Backend is healthy'
    } else {
      testResult.success = false
      testResult.status = `✗ HTTP ${response.status}`
      testResult.statusClass = 'status-error'
      testResult.details = response.data?.message || response.statusText || 'Server returned error'
    }
  } catch (error) {
    testResult.loading = false
    testResult.success = false
    
    if (error.code === 'ECONNREFUSED') {
      testResult.status = '✗ Connection Refused'
    } else if (error.code === 'ETIMEDOUT' || error.message?.includes('timeout')) {
      testResult.status = '✗ Timeout (10s exceeded)'
    } else if (error.code === 'ERR_NETWORK') {
      testResult.status = '✗ Network Error'
      testResult.details = 'Could not connect to backend. Check if server is running.'
    } else if (error.message?.includes('CORS')) {
      testResult.status = '✗ CORS Error'
      testResult.details = 'Cross-origin request blocked. Backend may need CORS configuration.'
    } else {
      testResult.status = `✗ ${error.message || 'Unknown Error'}`
      testResult.details = error.code || 'Check browser console for more details'
    }
    testResult.statusClass = 'status-error'
  }
  
  // Update the result in place
  const index = testResults.value.findIndex(t => t.url === url)
  if (index >= 0) {
    testResults.value[index] = testResult
  }
}

const testPort = (port) => {
  const url = `http://localhost:${port}`
  testBackendUrl(url)
}

const testCustomUrl = () => {
  if (customUrl.value) {
    // Ensure URL has protocol
    let url = customUrl.value
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = `http://${url}`
    }
    testBackendUrl(url)
  }
}

const useBackend = async (url) => {
  // Update backend URL in local storage
  localStorage.setItem('backendUrl', url)
  
  // Update in composable
  backendUrl.value = url
  
  // Recheck status
  await checkBackendStatus()
  
  // Emit event
  emit('backendChanged', url)
  
  // Update current config display
  await refreshTests()
}

const runFullDiagnostic = async () => {
  testResults.value = []
  
  // Test common ports
  for (const port of commonPorts.value) {
    await testPort(port)
  }
  
  // Test current backend URL
  if (currentBackendUrl.value) {
    await testBackendUrl(currentBackendUrl.value)
  }
}

const refreshTests = async () => {
  // Re-test all existing results
  const urls = testResults.value.map(t => t.url)
  testResults.value = []
  
  for (const url of urls) {
    await testBackendUrl(url)
  }
}

const testAllEndpoints = async () => {
  const endpoints = ['/api/health', '/api/classes', '/api/cache-status']
  const baseUrl = currentBackendUrl.value || expectedBackendUrl.value
  
  for (const endpoint of endpoints) {
    const testResult = {
      url: `${baseUrl}${endpoint}`,
      loading: true,
      success: false,
      status: 'Testing...',
      statusClass: 'status-testing',
      details: null
    }
    
    testResults.value.push(testResult)
    
    try {
      const response = await axios.get(`${baseUrl}${endpoint}`, { 
        timeout: 5000,
        validateStatus: () => true
      })
      
      testResult.loading = false
      
      if (response.status === 200) {
        testResult.success = true
        testResult.status = `✓ ${endpoint} - OK`
        testResult.statusClass = 'status-success'
      } else {
        testResult.success = false
        testResult.status = `✗ ${endpoint} - ${response.status}`
        testResult.statusClass = 'status-error'
      }
    } catch (error) {
      testResult.loading = false
      testResult.success = false
      testResult.status = `✗ ${endpoint} - Failed`
      testResult.statusClass = 'status-error'
      testResult.details = error.message
    }
  }
}

const exportReport = () => {
  const report = {
    timestamp: new Date().toISOString(),
    environment: {
      mode: import.meta.env.MODE,
      expectedBackend: expectedBackendUrl.value,
      currentBackend: currentBackendUrl.value,
      portMismatch: portMismatch.value
    },
    browser: browserInfo.value,
    connectionStatus: connectionStatus.value,
    testResults: testResults.value.map(t => ({
      url: t.url,
      status: t.status,
      success: t.success,
      responseTime: t.responseTime,
      details: t.details,
      timestamp: t.timestamp
    }))
  }
  
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `backend-diagnostic-${new Date().toISOString().replace(/[:.]/g, '-')}.json`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  // Test current backend on mount
  if (currentBackendUrl.value) {
    await testBackendUrl(currentBackendUrl.value)
  }
  
  // Also test expected backend if different
  if (expectedBackendUrl.value && expectedBackendUrl.value !== currentBackendUrl.value) {
    await testBackendUrl(expectedBackendUrl.value)
  }
  
  // Log any configuration issues for debugging
  if (portMismatch.value) {
    console.warn('Backend configuration mismatch:', portMismatch.value)
  }
  
  console.log('Backend Diagnostic Info:', {
    environment: import.meta.env.MODE,
    viteBackendUrl: import.meta.env.VITE_BACKEND_URL,
    expectedBackend: expectedBackendUrl.value,
    currentBackend: currentBackendUrl.value
  })
})
</script>

<style scoped>
.backend-diagnostic {
  background: rgba(20, 20, 40, 0.98);
  border: 1px solid rgba(100, 50, 200, 0.3);
  border-radius: 8px;
  padding: 20px;
  color: #ffffff;
  max-width: 600px;
  margin: 0 auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  max-height: 90vh;
  overflow-y: auto;
}

h3 {
  color: #9b72ff;
  margin-bottom: 20px;
  text-align: center;
}

h4 {
  color: #8060c0;
  margin-bottom: 10px;
  font-size: 0.9rem;
}

.diagnostic-section {
  margin-bottom: 25px;
  padding: 15px;
  background: rgba(30, 30, 50, 0.5);
  border-radius: 6px;
  border: 1px solid rgba(100, 50, 200, 0.2);
}

.config-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label {
  color: #8080a0;
  font-size: 0.9rem;
}

.value {
  color: #ffffff;
  font-family: monospace;
  font-size: 0.9rem;
}

.value.warning {
  color: #ffaa00;
}

.mismatch-warning {
  background: rgba(255, 170, 0, 0.1);
  padding: 8px;
  border-radius: 4px;
  margin-top: 8px;
}

.status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.85rem;
}

.status-connected {
  background: rgba(0, 255, 0, 0.2);
  color: #00ff00;
}

.status-disconnected {
  background: rgba(255, 0, 0, 0.2);
  color: #ff6060;
}

.test-results {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.test-item {
  padding: 8px;
  background: rgba(40, 40, 60, 0.5);
  border-radius: 4px;
  margin-bottom: 8px;
}

.test-item > div:first-child {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.test-url {
  flex: 1;
  font-family: monospace;
  font-size: 0.85rem;
  color: #a0a0c0;
}

.test-status {
  font-size: 0.85rem;
  padding: 2px 8px;
  border-radius: 4px;
  min-width: 120px;
  text-align: center;
}

.status-testing {
  background: rgba(255, 255, 0, 0.2);
  color: #ffff60;
}

.status-success {
  background: rgba(0, 255, 0, 0.2);
  color: #00ff00;
}

.status-error {
  background: rgba(255, 0, 0, 0.2);
  color: #ff6060;
}

.loading-spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.use-button {
  padding: 4px 12px;
  background: rgba(100, 50, 200, 0.3);
  border: 1px solid rgba(100, 50, 200, 0.5);
  color: #9b72ff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.use-button:hover {
  background: rgba(100, 50, 200, 0.5);
  border-color: #9b72ff;
}

.test-details {
  margin-top: 8px;
  padding: 6px 10px;
  background: rgba(20, 20, 30, 0.5);
  border-radius: 4px;
  font-size: 0.85rem;
  color: #a0a0c0;
  border-left: 3px solid rgba(100, 50, 200, 0.5);
}

.port-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.port-button {
  padding: 8px 16px;
  background: rgba(60, 60, 80, 0.5);
  border: 1px solid rgba(100, 50, 200, 0.3);
  color: #a0a0c0;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.port-button:hover {
  background: rgba(80, 80, 100, 0.5);
  border-color: rgba(100, 50, 200, 0.5);
  color: #ffffff;
}

.port-button.active {
  background: rgba(100, 50, 200, 0.3);
  border-color: #9b72ff;
  color: #9b72ff;
}

.manual-config {
  display: flex;
  gap: 10px;
}

.manual-config input {
  flex: 1;
  padding: 8px 12px;
  background: rgba(40, 40, 60, 0.5);
  border: 1px solid rgba(100, 50, 200, 0.3);
  color: #ffffff;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9rem;
}

.manual-config input::placeholder {
  color: #606080;
}

.manual-config input:focus {
  outline: none;
  border-color: #9b72ff;
}

.test-custom-button {
  padding: 8px 16px;
  background: rgba(100, 50, 200, 0.3);
  border: 1px solid rgba(100, 50, 200, 0.5);
  color: #9b72ff;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.test-custom-button:hover {
  background: rgba(100, 50, 200, 0.5);
  border-color: #9b72ff;
}

.diagnostic-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
}

.primary-button, .secondary-button {
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.primary-button {
  background: rgba(100, 50, 200, 0.3);
  border: 1px solid rgba(100, 50, 200, 0.5);
  color: #9b72ff;
}

.primary-button:hover {
  background: rgba(100, 50, 200, 0.5);
  border-color: #9b72ff;
  transform: translateY(-1px);
}

.secondary-button {
  background: rgba(60, 60, 80, 0.5);
  border: 1px solid rgba(100, 50, 200, 0.3);
  color: #a0a0c0;
}

.secondary-button:hover {
  background: rgba(80, 80, 100, 0.5);
  border-color: rgba(100, 50, 200, 0.5);
  color: #ffffff;
}
</style>