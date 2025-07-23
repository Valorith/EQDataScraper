import { ref, nextTick } from 'vue'

export function useTooltipPositioning() {
  const calculatePosition = async (mouseX, mouseY, tooltipEl, offset = 20) => {
    if (!tooltipEl) return { x: mouseX + offset, y: mouseY }
    
    await nextTick() // Ensure tooltip is rendered
    
    const windowWidth = window.innerWidth
    const windowHeight = window.innerHeight
    const scrollX = window.scrollX
    const scrollY = window.scrollY
    
    const tooltipRect = tooltipEl.getBoundingClientRect()
    const tooltipWidth = tooltipRect.width || 300 // fallback width
    const tooltipHeight = tooltipRect.height || 200 // fallback height
    
    let x, y
    
    // Horizontal positioning (following Char Browser pattern)
    // Place tooltip to the right or left of cursor based on available space
    if (mouseX > windowWidth / 2) {
      // Place to the left of cursor
      x = mouseX - tooltipWidth - offset
      // Ensure tooltip doesn't go off left edge
      if (x < 10) {
        x = 10
      }
    } else {
      // Place to the right of cursor  
      x = mouseX + offset
      // Ensure tooltip doesn't go off right edge
      if (x + tooltipWidth > windowWidth - 10) {
        x = windowWidth - tooltipWidth - 10
      }
    }
    
    // Vertical positioning with smart placement
    // Try to center tooltip on cursor Y position
    y = mouseY - (tooltipHeight / 2)
    
    // Adjust if tooltip goes off top edge
    if (y < scrollY + 10) {
      y = scrollY + 10
    }
    
    // Adjust if tooltip goes off bottom edge
    if (y + tooltipHeight > scrollY + windowHeight - 10) {
      y = scrollY + windowHeight - tooltipHeight - 10
      
      // If still doesn't fit, place above cursor
      if (y < scrollY + 10) {
        y = mouseY - tooltipHeight - offset
        if (y < scrollY + 10) {
          y = scrollY + 10
        }
      }
    }
    
    return { x, y }
  }
  
  const calculateTilePosition = (pinnedTooltips, newTooltipSize = { width: 300, height: 200 }) => {
    // Implement tooltip tiling for multiple pinned tooltips (Char Browser feature)
    if (pinnedTooltips.length === 0) {
      return { x: 100, y: 100 }
    }
    
    const spacing = 20
    const windowWidth = window.innerWidth
    const windowHeight = window.innerHeight
    
    // Find a position that doesn't overlap with existing tooltips
    for (let row = 0; row < 5; row++) {
      for (let col = 0; col < 4; col++) {
        const x = 100 + (col * (newTooltipSize.width + spacing))
        const y = 100 + (row * (newTooltipSize.height + spacing))
        
        // Check if position is within viewport
        if (x + newTooltipSize.width > windowWidth - 10 || 
            y + newTooltipSize.height > windowHeight - 10) {
          continue
        }
        
        // Check if position overlaps with existing tooltips
        const overlaps = pinnedTooltips.some(tooltip => {
          const tooltipX = tooltip.position?.x || 0
          const tooltipY = tooltip.position?.y || 0
          const tooltipWidth = tooltip.size?.width || 300
          const tooltipHeight = tooltip.size?.height || 200
          
          return !(x + newTooltipSize.width < tooltipX || 
                   x > tooltipX + tooltipWidth ||
                   y + newTooltipSize.height < tooltipY ||
                   y > tooltipY + tooltipHeight)
        })
        
        if (!overlaps) {
          return { x, y }
        }
      }
    }
    
    // Fallback: cascade position
    const lastTooltip = pinnedTooltips[pinnedTooltips.length - 1]
    return {
      x: (lastTooltip.position?.x || 100) + 30,
      y: (lastTooltip.position?.y || 100) + 30
    }
  }
  
  const isPositionInViewport = (x, y, width, height) => {
    const windowWidth = window.innerWidth
    const windowHeight = window.innerHeight
    const scrollX = window.scrollX
    const scrollY = window.scrollY
    
    return (
      x >= scrollX &&
      y >= scrollY &&
      x + width <= scrollX + windowWidth &&
      y + height <= scrollY + windowHeight
    )
  }
  
  const constrainToViewport = (x, y, width, height, margin = 10) => {
    const windowWidth = window.innerWidth
    const windowHeight = window.innerHeight
    const scrollX = window.scrollX
    const scrollY = window.scrollY
    
    // Constrain X
    if (x < scrollX + margin) {
      x = scrollX + margin
    } else if (x + width > scrollX + windowWidth - margin) {
      x = scrollX + windowWidth - width - margin
    }
    
    // Constrain Y
    if (y < scrollY + margin) {
      y = scrollY + margin
    } else if (y + height > scrollY + windowHeight - margin) {
      y = scrollY + windowHeight - height - margin
    }
    
    return { x, y }
  }
  
  return {
    calculatePosition,
    calculateTilePosition,
    isPositionInViewport,
    constrainToViewport
  }
}