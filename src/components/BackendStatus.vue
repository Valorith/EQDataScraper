<template>
  <div class="backend-status" :class="statusClass" v-if="showStatus">
    <div class="status-indicator">
      <span class="status-dot" :class="{ 'pulse': isChecking }"></span>
      <span class="status-text">{{ statusMessage }}</span>
    </div>
    <button 
      v-if="!isConnected && !isChecking" 
      @click="refresh" 
      class="retry-button"
      title="Retry connection"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21.5 2v6h-6M2.5 22v-6h6M2 12c0-5.523 4.477-10 10-10 1.5 0 2.923.33 4.2.916M22 12c0 5.523-4.477 10-10 10-1.5 0-2.923-.33-4.2-.916"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useBackendStatus } from '../composables/useBackendStatus'
import { useUserStore } from '../stores/userStore'

const props = defineProps({
  alwaysShow: {
    type: Boolean,
    default: false
  }
})

const userStore = useUserStore()

const { 
  isConnected, 
  isChecking, 
  errorCount,
  statusMessage,
  statusClass,
  refresh 
} = useBackendStatus()

const showStatus = computed(() => {
  // Only show for admin users
  if (userStore.user?.role !== 'admin') {
    return false
  }
  
  return props.alwaysShow || !isConnected.value || errorCount.value > 0
})
</script>

<style scoped>
.backend-status {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(32, 33, 36, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.backend-status.success .status-dot {
  background-color: #4ade80;
  box-shadow: 0 0 8px rgba(74, 222, 128, 0.5);
}

.backend-status.warning .status-dot {
  background-color: #fbbf24;
  box-shadow: 0 0 8px rgba(251, 191, 36, 0.5);
}

.backend-status.error .status-dot {
  background-color: #f87171;
  box-shadow: 0 0 8px rgba(248, 113, 113, 0.5);
}

.status-dot.pulse {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(0.8);
  }
}

.status-text {
  color: #e5e7eb;
}

.retry-button {
  background: rgba(139, 92, 246, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.5);
  border-radius: 6px;
  padding: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.retry-button:hover {
  background: rgba(139, 92, 246, 0.3);
  border-color: rgba(139, 92, 246, 0.8);
  transform: rotate(90deg);
}

.retry-button svg {
  color: #e5e7eb;
}

/* Mobile responsive */
@media (max-width: 640px) {
  .backend-status {
    bottom: 10px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 13px;
    max-width: calc(100% - 20px);
  }
}
</style>