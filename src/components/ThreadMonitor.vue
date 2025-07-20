<template>
  <div v-if="visible" class="thread-monitor">
    <div class="monitor-header">
      <h3>Thread Monitor</h3>
      <button @click="toggleMinimize" class="minimize-btn">
        {{ minimized ? '📊' : '➖' }}
      </button>
      <button @click="close" class="close-btn">✖</button>
    </div>
    
    <div v-if="!minimized" class="monitor-content">
      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ status.runningOperations.length }}</div>
          <div class="stat-label">Running Ops</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ status.activeWorkers }}</div>
          <div class="stat-label">Workers</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ status.activeTimers + status.activeIntervals }}</div>
          <div class="stat-label">Timers</div>
        </div>
        <div class="stat-card" :class="{ warning: memoryUsage > 80 }">
          <div class="stat-value">{{ memoryUsage }}%</div>
          <div class="stat-label">Memory</div>
        </div>
      </div>

      <!-- Problematic Operations -->
      <div v-if="problematicOps.length > 0" class="problematic-section">
        <h4>⚠️ Long Running Operations</h4>
        <div v-for="op in problematicOps" :key="op.id" class="problematic-op">
          <div class="op-name">{{ op.name }}</div>
          <div class="op-duration">{{ formatDuration(op.duration) }}</div>
          <button @click="viewDetails(op)" class="detail-btn">Details</button>
        </div>
      </div>

      <!-- Running Operations -->
      <div class="operations-section">
        <h4>Running Operations</h4>
        <div v-if="status.runningOperations.length === 0" class="empty-state">
          No operations running
        </div>
        <div v-else class="operations-list">
          <div v-for="op in status.runningOperations" :key="op.id" class="operation-item">
            <div class="op-info">
              <span class="op-name">{{ op.name }}</span>
              <span class="op-id">#{{ op.id }}</span>
            </div>
            <div class="op-duration">{{ formatDuration(op.duration) }}</div>
            <div class="op-progress">
              <div class="progress-bar" :style="{ width: getProgressWidth(op.duration) }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Performance Metrics -->
      <div class="metrics-section">
        <h4>Performance Metrics</h4>
        <div class="metrics-table">
          <table>
            <thead>
              <tr>
                <th>Operation</th>
                <th>Count</th>
                <th>Avg</th>
                <th>Max</th>
                <th>Failures</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(metric, name) in status.performanceMetrics" :key="name">
                <td>{{ name }}</td>
                <td>{{ metric.count }}</td>
                <td>{{ formatDuration(metric.averageDuration) }}</td>
                <td>{{ formatDuration(metric.maxDuration) }}</td>
                <td :class="{ error: metric.failures > 0 }">{{ metric.failures }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Controls -->
      <div class="controls">
        <button @click="refresh" class="control-btn">🔄 Refresh</button>
        <button @click="forceCleanup" class="control-btn danger">🧹 Force Cleanup</button>
        <button @click="exportReport" class="control-btn">📊 Export Report</button>
      </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="selectedOp" class="detail-modal" @click.self="selectedOp = null">
      <div class="detail-content">
        <h3>Operation Details</h3>
        <div class="detail-info">
          <div><strong>Name:</strong> {{ selectedOp.name }}</div>
          <div><strong>ID:</strong> {{ selectedOp.id }}</div>
          <div><strong>Duration:</strong> {{ formatDuration(selectedOp.duration) }}</div>
          <div v-if="selectedOp.metadata && Object.keys(selectedOp.metadata).length > 0">
            <strong>Metadata:</strong>
            <pre>{{ JSON.stringify(selectedOp.metadata, null, 2) }}</pre>
          </div>
          <div v-if="selectedOp.stackTrace" class="stack-trace">
            <strong>Stack Trace:</strong>
            <pre>{{ selectedOp.stackTrace }}</pre>
          </div>
        </div>
        <button @click="selectedOp = null" class="close-detail-btn">Close</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { threadManager } from '@/utils/threadManager'

export default {
  name: 'ThreadMonitor',
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const minimized = ref(false)
    const status = ref({
      runningOperations: [],
      activeWorkers: 0,
      activeTimers: 0,
      activeIntervals: 0,
      performanceMetrics: {}
    })
    const problematicOps = ref([])
    const selectedOp = ref(null)
    const refreshInterval = ref(null)

    const memoryUsage = computed(() => {
      if (!performance.memory) return 0
      return Math.round((performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit) * 100)
    })

    const refresh = () => {
      status.value = threadManager.getStatus()
      problematicOps.value = threadManager.getProblematicOperations()
    }

    const toggleMinimize = () => {
      minimized.value = !minimized.value
    }

    const close = () => {
      emit('close')
    }

    const formatDuration = (ms) => {
      if (ms < 1000) return `${Math.round(ms)}ms`
      if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
      return `${(ms / 60000).toFixed(1)}m`
    }

    const getProgressWidth = (duration) => {
      // Show progress based on warning threshold (5s)
      const percentage = Math.min((duration / 5000) * 100, 100)
      return `${percentage}%`
    }

    const viewDetails = (op) => {
      selectedOp.value = op
    }

    const forceCleanup = () => {
      if (confirm('Force cleanup all operations older than 60 seconds?')) {
        const cleaned = threadManager.forceCleanup()
        alert(`Cleaned ${cleaned} operations/workers`)
        refresh()
      }
    }

    const exportReport = () => {
      const report = threadManager.generateDebugReport()
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `thread-report-${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
    }

    onMounted(() => {
      refresh()
      // Auto-refresh every second
      refreshInterval.value = setInterval(refresh, 1000)
    })

    onUnmounted(() => {
      if (refreshInterval.value) {
        clearInterval(refreshInterval.value)
      }
    })

    return {
      minimized,
      status,
      problematicOps,
      selectedOp,
      memoryUsage,
      refresh,
      toggleMinimize,
      close,
      formatDuration,
      getProgressWidth,
      viewDetails,
      forceCleanup,
      exportReport
    }
  }
}
</script>

<style scoped>
.thread-monitor {
  position: fixed;
  top: 80px;
  right: 20px;
  width: 450px;
  background: rgba(20, 25, 40, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(147, 112, 219, 0.3);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  z-index: 1000;
  font-family: 'Inter', sans-serif;
}

.monitor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(147, 112, 219, 0.15);
  border-bottom: 1px solid rgba(147, 112, 219, 0.2);
  border-radius: 12px 12px 0 0;
}

.monitor-header h3 {
  margin: 0;
  font-size: 16px;
  color: white;
  font-weight: 600;
}

.minimize-btn,
.close-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  font-size: 16px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.minimize-btn:hover,
.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.monitor-content {
  padding: 16px;
  max-height: 600px;
  overflow-y: auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
}

.stat-card.warning {
  border-color: rgba(255, 193, 7, 0.5);
  background: rgba(255, 193, 7, 0.1);
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #9370db;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.problematic-section {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 20px;
}

.problematic-section h4 {
  margin: 0 0 12px 0;
  color: #fca5a5;
  font-size: 14px;
}

.problematic-op {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  margin-bottom: 8px;
}

.op-name {
  font-weight: 500;
  color: white;
  flex: 1;
}

.op-duration {
  color: #fca5a5;
  font-size: 14px;
  margin: 0 12px;
}

.detail-btn {
  background: rgba(147, 112, 219, 0.2);
  border: 1px solid rgba(147, 112, 219, 0.3);
  color: white;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.detail-btn:hover {
  background: rgba(147, 112, 219, 0.3);
  border-color: rgba(147, 112, 219, 0.5);
}

.operations-section,
.metrics-section {
  margin-bottom: 20px;
}

.operations-section h4,
.metrics-section h4 {
  margin: 0 0 12px 0;
  color: white;
  font-size: 14px;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  padding: 20px;
  font-style: italic;
}

.operations-list {
  space-y: 8px;
}

.operation-item {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
}

.op-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.op-id {
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}

.op-progress {
  margin-top: 8px;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #9370db, #c8a8ff);
  transition: width 0.3s ease;
}

.metrics-table {
  overflow-x: auto;
}

.metrics-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.metrics-table th {
  text-align: left;
  padding: 8px;
  background: rgba(147, 112, 219, 0.1);
  color: white;
  font-weight: 600;
  border-bottom: 1px solid rgba(147, 112, 219, 0.2);
}

.metrics-table td {
  padding: 8px;
  color: rgba(255, 255, 255, 0.8);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.metrics-table td.error {
  color: #fca5a5;
  font-weight: 600;
}

.controls {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.control-btn {
  flex: 1;
  background: rgba(147, 112, 219, 0.2);
  border: 1px solid rgba(147, 112, 219, 0.3);
  color: white;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.control-btn:hover {
  background: rgba(147, 112, 219, 0.3);
  border-color: rgba(147, 112, 219, 0.5);
}

.control-btn.danger {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.3);
}

.control-btn.danger:hover {
  background: rgba(239, 68, 68, 0.3);
  border-color: rgba(239, 68, 68, 0.5);
}

.detail-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
  padding: 20px;
}

.detail-content {
  background: rgba(20, 25, 40, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(147, 112, 219, 0.3);
  border-radius: 12px;
  padding: 24px;
  max-width: 600px;
  width: 100%;
  max-height: 80vh;
  overflow-y: auto;
}

.detail-content h3 {
  margin: 0 0 16px 0;
  color: white;
}

.detail-info {
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
}

.detail-info > div {
  margin-bottom: 12px;
}

.detail-info strong {
  color: white;
}

.detail-info pre {
  background: rgba(0, 0, 0, 0.3);
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 12px;
  margin-top: 8px;
}

.stack-trace {
  margin-top: 16px;
}

.close-detail-btn {
  background: rgba(147, 112, 219, 0.2);
  border: 1px solid rgba(147, 112, 219, 0.3);
  color: white;
  padding: 8px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  margin-top: 16px;
  transition: all 0.2s;
}

.close-detail-btn:hover {
  background: rgba(147, 112, 219, 0.3);
  border-color: rgba(147, 112, 219, 0.5);
}

/* Scrollbar styling */
.monitor-content::-webkit-scrollbar,
.detail-content::-webkit-scrollbar {
  width: 8px;
}

.monitor-content::-webkit-scrollbar-track,
.detail-content::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.monitor-content::-webkit-scrollbar-thumb,
.detail-content::-webkit-scrollbar-thumb {
  background: rgba(147, 112, 219, 0.5);
  border-radius: 4px;
}

.monitor-content::-webkit-scrollbar-thumb:hover,
.detail-content::-webkit-scrollbar-thumb:hover {
  background: rgba(147, 112, 219, 0.7);
}
</style>