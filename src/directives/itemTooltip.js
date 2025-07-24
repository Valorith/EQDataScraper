import { useTooltipStore } from '../stores/tooltips'

export const vItemTooltip = {
  mounted(el, binding, vnode) {
    if (!binding.value) {
      // No item equipped in this slot - skip tooltip setup
      return
    }
    
    const { itemId, allowPin = false, delay = 300 } = binding.value || {}
    
    if (!itemId) {
      console.warn('v-item-tooltip: itemId is required, received:', binding.value)
      return
    }
    
    console.log('Tooltip setup for item:', itemId)
    
    let showTimeout
    let hideTimeout
    let mouseX = 0
    let mouseY = 0
    
    const tooltipStore = useTooltipStore()
    
    const showTooltip = async (event) => {
      
      // Clear any pending hide
      if (hideTimeout) {
        clearTimeout(hideTimeout)
        hideTimeout = null
      }
      
      // Skip if tooltip is already visible (pinned or active)
      if (tooltipStore.isTooltipVisible(itemId)) {
        console.log('Tooltip already visible for itemId:', itemId)
        return
      }
      
      // Update mouse position
      mouseX = event.pageX
      mouseY = event.pageY
      
      // Clear any existing show timeout
      if (showTimeout) {
        clearTimeout(showTimeout)
      }
      
      // Show tooltip after delay
      showTimeout = setTimeout(async () => {
        try {
          await tooltipStore.showTooltip(itemId, {
            mouseX,
            mouseY,
            allowPin,
            triggerEl: el
          })
        } catch (error) {
          console.error('Failed to show tooltip:', error)
        }
        showTimeout = null
      }, delay)
    }
    
    const hideTooltip = () => {
      // Clear any pending show
      if (showTimeout) {
        clearTimeout(showTimeout)
        showTimeout = null
      }
      
      // Don't hide immediately - add small delay to allow moving to tooltip
      hideTimeout = setTimeout(() => {
        tooltipStore.hideTooltip(itemId)
        hideTimeout = null
      }, 100)
    }
    
    const updatePosition = (event) => {
      mouseX = event.pageX
      mouseY = event.pageY
      
      // Update tooltip position if it's currently visible (but not pinned)
      const tooltipState = tooltipStore.getTooltipState(itemId)
      if (tooltipState && !tooltipState.isPinned) {
        tooltipStore.updateTooltipPosition(itemId, mouseX, mouseY)
      }
    }
    
    // Event listeners
    const onMouseEnter = (event) => {
      showTooltip(event)
    }
    
    const onMouseLeave = () => {
      hideTooltip()
    }
    
    const onMouseMove = (event) => {
      updatePosition(event)
    }
    
    // Click handler for quick access (optional)
    const onClick = (event) => {
      // If shift+click, toggle pin
      if (event.shiftKey && allowPin) {
        event.preventDefault()
        tooltipStore.toggleTooltipPin(itemId)
      }
    }
    
    // Add event listeners
    el.addEventListener('mouseenter', onMouseEnter)
    el.addEventListener('mouseleave', onMouseLeave)
    el.addEventListener('mousemove', onMouseMove)
    el.addEventListener('click', onClick)
    
    // Add tooltip cursor style
    el.style.cursor = 'pointer'
    el.setAttribute('data-tooltip-item', itemId)
    
    // Store cleanup function
    el._tooltipCleanup = () => {
      if (showTimeout) {
        clearTimeout(showTimeout)
      }
      if (hideTimeout) {
        clearTimeout(hideTimeout)
      }
      
      el.removeEventListener('mouseenter', onMouseEnter)
      el.removeEventListener('mouseleave', onMouseLeave)
      el.removeEventListener('mousemove', onMouseMove)
      el.removeEventListener('click', onClick)
      
      // Clean up tooltip state
      tooltipStore.hideTooltip(itemId)
    }
    
    // Store directive config for updates
    el._tooltipConfig = { itemId, allowPin, delay }
  },
  
  updated(el, binding) {
    const newConfig = binding.value || {}
    const oldConfig = el._tooltipConfig || {}
    
    // If itemId changed, we need to remount
    if (newConfig.itemId !== oldConfig.itemId) {
      // Clean up old
      if (el._tooltipCleanup) {
        el._tooltipCleanup()
      }
      
      // Remount with new config
      vItemTooltip.mounted(el, binding)
    } else {
      // Just update config
      el._tooltipConfig = { ...oldConfig, ...newConfig }
    }
  },
  
  unmounted(el) {
    if (el._tooltipCleanup) {
      el._tooltipCleanup()
    }
  }
}

// Install function for Vue app
export function installTooltipDirective(app) {
  app.directive('item-tooltip', vItemTooltip)
}