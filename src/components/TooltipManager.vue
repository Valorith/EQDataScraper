<template>
  <div class="tooltip-manager">
    <!-- Render all active tooltips -->
    <ItemTooltip
      v-for="tooltip in allActiveTooltips"
      :key="tooltip.itemId"
      :visible="tooltip.visible"
      :item-id="tooltip.itemId"
      :item-data="tooltip.itemData"
      :loading="tooltip.loading"
      :error="tooltip.error"
      :position="tooltip.position"
      :allow-pin="tooltip.allowPin"
      :is-pinned="tooltip.isPinned"
      @close="handleTooltipClose(tooltip.itemId)"
      @toggle-pin="handleTooltipPin(tooltip.itemId)"
      @mouse-enter="handleTooltipMouseEnter(tooltip.itemId)"
      @mouse-leave="handleTooltipMouseLeave(tooltip.itemId)"
    />
  </div>
</template>

<script setup>
import { computed, watch, nextTick } from 'vue'
import { useTooltipStore } from '../stores/tooltips'
import { useTooltipPositioning } from '../composables/useTooltipPositioning'
import ItemTooltip from './ItemTooltip.vue'

const tooltipStore = useTooltipStore()
const { calculatePosition } = useTooltipPositioning()

const allActiveTooltips = computed(() => {
  return tooltipStore.getAllActiveTooltips
})

const handleTooltipClose = (itemId) => {
  tooltipStore.closeTooltip(itemId)
}

const handleTooltipPin = (itemId) => {
  tooltipStore.toggleTooltipPin(itemId)
}

const handleTooltipMouseEnter = (itemId) => {
  // Keep tooltip visible when hovering over it
  // This prevents it from hiding when moving from trigger to tooltip
}

const handleTooltipMouseLeave = (itemId) => {
  // Hide tooltip when leaving it (unless pinned)
  const tooltipState = tooltipStore.getTooltipState(itemId)
  if (tooltipState && !tooltipState.isPinned) {
    // Small delay to allow moving back to tooltip
    setTimeout(() => {
      const currentState = tooltipStore.getTooltipState(itemId)
      if (currentState && !currentState.isPinned) {
        tooltipStore.hideTooltip(itemId)
      }
    }, 100)
  }
}

// Disable problematic watch for now
// watch(
//   () => tooltipStore.activeTooltips,
//   async (newTooltips) => {
//     // This was causing infinite loops - commenting out for debugging
//   },
//   { deep: true }
// )

// Handle escape key to close all tooltips
const handleKeydown = (event) => {
  if (event.key === 'Escape') {
    tooltipStore.closeAllTooltips()
  }
}

// Add escape key listener
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', handleKeydown)
}

// Cleanup on unmount
import { onUnmounted } from 'vue'
onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('keydown', handleKeydown)
  }
})
</script>

<style scoped>
.tooltip-manager {
  pointer-events: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99998;
}
</style>