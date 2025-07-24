import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { useTooltipPositioning } from '../composables/useTooltipPositioning'
import { getApiBaseUrl } from '../config/api'

export const useTooltipStore = defineStore('tooltips', () => {
  // State
  const cachedItems = ref(new Map()) // itemId -> item data
  const loadingItems = ref(new Set()) // itemIds currently being loaded
  const activeTooltips = ref(new Map()) // itemId -> tooltip state
  const pinnedTooltips = ref(new Map()) // itemId -> tooltip state for pinned tooltips
  const loadingPromises = ref(new Map()) // itemId -> promise for loading items
  
  // Use positioning utility
  const { calculatePosition, calculateTilePosition } = useTooltipPositioning()
  
  // Computed
  const activePinnedTooltips = computed(() => {
    return Array.from(pinnedTooltips.value.values())
  })
  
  // Actions
  const preloadInventoryItems = async (characterId) => {
    try {
      console.log(`Preloading inventory items for character ${characterId}`)
      
      // Get character inventory to extract item IDs
      const inventoryResponse = await axios.get(`${getApiBaseUrl()}/api/characters/${characterId}/inventory`)
      const inventory = inventoryResponse.data
      
      // Extract unique item IDs from inventory
      const itemIds = new Set()
      
      // Equipment slots
      if (inventory.equipment) {
        Object.values(inventory.equipment).forEach(item => {
          if (item?.id) itemIds.add(item.id)
        })
      }
      
      // Inventory bags
      if (inventory.inventorySlots) {
        Object.values(inventory.inventorySlots).forEach(bag => {
          if (bag?.items) {
            Object.values(bag.items).forEach(item => {
              if (item?.id) itemIds.add(item.id)
            })
          }
        })
      }
      
      const uniqueItemIds = Array.from(itemIds)
      console.log(`Found ${uniqueItemIds.length} unique items to preload`)
      
      if (uniqueItemIds.length === 0) return
      
      // Bulk fetch all item data
      const itemsResponse = await axios.post(`${getApiBaseUrl()}/api/items/bulk`, {
        ids: uniqueItemIds
      })
      
      // Cache all items
      itemsResponse.data.forEach(item => {
        cachedItems.value.set(item.id, item)
      })
      
      console.log(`Preloaded ${itemsResponse.data.length} items into cache`)
      
    } catch (error) {
      console.error('Failed to preload inventory items:', error)
    }
  }
  
  const getItemData = async (itemId) => {
    // Return cached data if available
    if (cachedItems.value.has(itemId)) {
      return cachedItems.value.get(itemId)
    }
    
    // If already loading, wait for existing request
    if (loadingPromises.value.has(itemId)) {
      return await loadingPromises.value.get(itemId)
    }
    
    // Start loading
    loadingItems.value.add(itemId)
    
    const loadPromise = (async () => {
      try {
        const response = await axios.get(`${getApiBaseUrl()}/api/items/${itemId}/tooltip`)
        const itemData = response.data
        
        // Cache the item data
        cachedItems.value.set(itemId, itemData)
        return itemData
        
      } catch (error) {
        console.error(`Failed to load item ${itemId}:`, error)
        throw error
      } finally {
        loadingItems.value.delete(itemId)
        loadingPromises.value.delete(itemId)
      }
    })()
    
    loadingPromises.value.set(itemId, loadPromise)
    return loadPromise
  }
  
  const showTooltip = async (itemId, options = {}) => {
    const {
      mouseX,
      mouseY,
      allowPin = false,
      triggerEl = null
    } = options
    
    // Don't show tooltip if already pinned (unless forced)
    if (pinnedTooltips.value.has(itemId) && !options.force) {
      return
    }
    
    // Create tooltip state
    const tooltipState = {
      itemId,
      visible: true,
      loading: !cachedItems.value.has(itemId),
      error: false,
      itemData: cachedItems.value.get(itemId) || null,
      allowPin,
      isPinned: false,
      position: { x: mouseX || 0, y: mouseY || 0 },
      triggerEl
    }
    
    activeTooltips.value.set(itemId, tooltipState)
    
    // Load item data if not cached
    if (!tooltipState.itemData) {
      try {
        const itemData = await getItemData(itemId)
        tooltipState.itemData = itemData
        tooltipState.loading = false
      } catch (error) {
        tooltipState.loading = false
        tooltipState.error = true
      }
    }
    
    // Calculate position after tooltip is rendered
    if (tooltipState.visible) {
      // Position will be recalculated by the component when it mounts
    }
  }
  
  const hideTooltip = (itemId) => {
    // Don't hide pinned tooltips
    if (pinnedTooltips.value.has(itemId)) {
      return
    }
    
    activeTooltips.value.delete(itemId)
  }
  
  const pinTooltip = (itemId) => {
    const tooltip = activeTooltips.value.get(itemId)
    if (!tooltip) return
    
    // Calculate tile position for pinned tooltip
    const pinnedArray = Array.from(pinnedTooltips.value.values())
    const tilePosition = calculateTilePosition(pinnedArray)
    
    // Create pinned tooltip state
    const pinnedTooltip = {
      ...tooltip,
      isPinned: true,
      position: tilePosition
    }
    
    pinnedTooltips.value.set(itemId, pinnedTooltip)
    activeTooltips.value.delete(itemId)
  }
  
  const unpinTooltip = (itemId) => {
    pinnedTooltips.value.delete(itemId)
  }
  
  const toggleTooltipPin = (itemId) => {
    if (pinnedTooltips.value.has(itemId)) {
      unpinTooltip(itemId)
    } else {
      pinTooltip(itemId)
    }
  }
  
  const closeTooltip = (itemId) => {
    activeTooltips.value.delete(itemId)
    pinnedTooltips.value.delete(itemId)
  }
  
  const closeAllTooltips = () => {
    activeTooltips.value.clear()
    pinnedTooltips.value.clear()
  }
  
  const updateTooltipPosition = async (itemId, mouseX, mouseY, tooltipEl) => {
    const tooltip = activeTooltips.value.get(itemId) || pinnedTooltips.value.get(itemId)
    if (!tooltip || tooltip.isPinned) return
    
    const position = await calculatePosition(mouseX, mouseY, tooltipEl)
    tooltip.position = position
  }
  
  const getAllActiveTooltips = computed(() => {
    const all = []
    
    // Add regular tooltips
    activeTooltips.value.forEach(tooltip => {
      all.push(tooltip)
    })
    
    // Add pinned tooltips
    pinnedTooltips.value.forEach(tooltip => {
      all.push(tooltip)
    })
    
    return all
  })
  
  const isItemLoading = (itemId) => {
    return loadingItems.value.has(itemId)
  }
  
  const isTooltipVisible = (itemId) => {
    return activeTooltips.value.has(itemId) || pinnedTooltips.value.has(itemId)
  }
  
  const getTooltipState = (itemId) => {
    return activeTooltips.value.get(itemId) || pinnedTooltips.value.get(itemId)
  }
  
  const clearCache = () => {
    cachedItems.value.clear()
    loadingItems.value.clear()
    loadingPromises.value.clear()
  }
  
  return {
    // State
    cachedItems,
    loadingItems,
    activeTooltips,
    pinnedTooltips,
    
    // Computed
    activePinnedTooltips,
    getAllActiveTooltips,
    
    // Actions
    preloadInventoryItems,
    getItemData,
    showTooltip,
    hideTooltip,
    pinTooltip,
    unpinTooltip,
    toggleTooltipPin,
    closeTooltip,
    closeAllTooltips,
    updateTooltipPosition,
    
    // Getters
    isItemLoading,
    isTooltipVisible,
    getTooltipState,
    clearCache
  }
})