<template>
  <div v-if="visible" :class="['loading-modal-overlay', { 'full-screen': fullScreen }]">
    <div class="loading-modal-content">
      <img 
        v-if="showIcon"
        :src="iconSrc" 
        :alt="iconAlt"
        class="loading-modal-icon"
        @error="handleIconError"
      />
      <span class="loading-modal-text">{{ text }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  text: {
    type: String,
    default: 'Loading'
  },
  fullScreen: {
    type: Boolean,
    default: false
  },
  showIcon: {
    type: Boolean,
    default: true
  },
  customIcon: {
    type: String,
    default: null
  },
  randomClassIcon: {
    type: Boolean,
    default: true
  },
  timeoutMs: {
    type: Number,
    default: 10000 // 10 seconds default timeout
  }
})

const emit = defineEmits(['timeout'])

// EverQuest classes for loading icons
const classNames = [
  'warrior',
  'cleric',
  'paladin',
  'ranger',
  'shadowknight',
  'druid',
  'monk',
  'bard',
  'rogue',
  'shaman',
  'necromancer',
  'wizard',
  'magician',
  'enchanter',
  'beastlord',
  'berserker'
]

const currentIcon = ref('')
const timeoutId = ref(null)

// Select a random class icon when component becomes visible
// Also handle timeout logic
watch(() => props.visible, (newVal) => {
  if (newVal && props.randomClassIcon && !props.customIcon) {
    currentIcon.value = classNames[Math.floor(Math.random() * classNames.length)]
  }
  
  // Handle timeout
  if (newVal) {
    // Start timeout when modal becomes visible
    timeoutId.value = setTimeout(() => {
      console.warn(`LoadingModal timeout reached after ${props.timeoutMs}ms`)
      emit('timeout')
    }, props.timeoutMs)
  } else {
    // Clear timeout when modal is hidden
    if (timeoutId.value) {
      clearTimeout(timeoutId.value)
      timeoutId.value = null
    }
  }
})

const iconSrc = computed(() => {
  if (props.customIcon) {
    return props.customIcon
  }
  return `/icons/${currentIcon.value}.gif`
})

const iconAlt = computed(() => {
  if (props.customIcon) {
    return 'Loading icon'
  }
  return currentIcon.value
})

const handleIconError = (event) => {
  // Fallback to a default icon if the class icon fails to load
  event.target.style.display = 'none'
}

// Cleanup timeout on component unmount
onUnmounted(() => {
  if (timeoutId.value) {
    clearTimeout(timeoutId.value)
    timeoutId.value = null
  }
})
</script>

<style scoped>
@import '../style-constants.css';

/* Overlay Styles */
.loading-modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  border-radius: 20px;
}

.loading-modal-overlay.full-screen {
  position: fixed;
  border-radius: 0;
  z-index: 9999;
}

/* Content Container */
.loading-modal-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

/* Icon Styles */
.loading-modal-icon {
  width: 64px;
  height: 128px;
  object-fit: contain;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  filter: drop-shadow(0 0 20px rgba(102, 126, 234, 0.6));
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

/* Text Styles */
.loading-modal-text {
  font-size: 1.5rem;
  font-weight: 600;
  color: #f7fafc;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Animation */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .loading-modal-icon {
    width: 48px;
    height: 96px;
  }
  
  .loading-modal-text {
    font-size: 1.2rem;
  }
}
</style>