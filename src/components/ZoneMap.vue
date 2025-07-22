<template>
  <div class="zone-map-wrapper">
    <LoadingModal :visible="loading" text="Loading map..." />
    
    <!-- Map Controls -->
    <div class="map-controls">
      <button @click="zoomIn" class="control-btn zoom-in-btn" title="Zoom In">
        <span class="btn-icon">+</span>
      </button>
      <button @click="zoomOut" class="control-btn zoom-out-btn" title="Zoom Out">
        <span class="btn-icon">−</span>
      </button>
      <button @click="resetView" class="control-btn reset-btn" title="Reset View">
        <span class="btn-icon">⌂</span>
      </button>
      <div class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</div>
    </div>
    
    <!-- Coordinate Indicator -->
    <div v-if="showCoordinates && currentCoords" class="coordinate-indicator">
      <div class="cursor-icon">⌖</div>
      <div class="coord-values">
        <span class="coord-axis">X: {{ currentCoords.x }}</span>
        <span class="coord-axis">Y: {{ currentCoords.y }}</span>
      </div>
    </div>
    
    <!-- Dropped Pin Coordinates -->
    <div v-if="droppedPin" class="pin-coordinate-indicator">
      <div class="coord-label">Dropped Pin:</div>
      <div class="coord-values">
        <span class="coord-axis">X: {{ droppedPin.gameX }}</span>
        <span class="coord-axis">Y: {{ droppedPin.gameY }}</span>
      </div>
      <button @click="clearPin" class="clear-pin-btn">Clear Pin</button>
    </div>
    
    <!-- Fullscreen Button -->
    <div class="fullscreen-container">
      <button 
        @click="toggleFullscreen"
        class="fullscreen-btn"
        :title="isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'"
      >
        <span class="fullscreen-icon" v-if="!isFullscreen">⛶</span>
        <span class="fullscreen-icon" v-else>⊡</span>
      </button>
      <span v-if="isFullscreen" class="esc-hint">Esc</span>
    </div>

    <!-- Map Container -->
    <div 
      ref="mapContainer"
      class="map-container"
      @mousedown="startPan"
      @mousemove="updatePanAndCoords"
      @mouseup="endPan"
      @mouseleave="endPan"
      @wheel="handleWheel"
      @dblclick="handleDoubleClick"
      @contextmenu="handleRightClick"
    >
      <svg 
        ref="mapSvg"
        class="map-svg"
        :viewBox="viewBox"
        :style="{
          transform: `translate(${panX}px, ${panY}px) scale(${zoomLevel})`,
          transformOrigin: '0 0'
        }"
      >
        
        <!-- Map Lines -->
        <g class="map-lines">
          <line
            v-for="(line, index) in processedLines"
            :key="index"
            :x1="line.x1"
            :y1="line.y1"
            :x2="line.x2"
            :y2="line.y2"
            :stroke="line.color"
            :stroke-width="mapLineWidth"
            stroke-linecap="round"
          />
        </g>
        
        <!-- NPC Pins -->
        <g class="npc-pins">
          <g
            v-for="npc in npcLocations"
            :key="`${npc.id}-${npc.x}-${npc.y}`"
            :class="['npc-pin', { 'newly-plotted': npc.isNewlyPlotted }]"
            @click="$emit('npc-click', npc)"
            :transform="`translate(${npc.x}, ${npc.y}) scale(${npcIconScale})`"
          >
            <!-- Extra Large Outer Glow Ring -->
            <circle
              cx="0"
              cy="0"
              r="25"
              fill="none"
              :stroke="npc.color || '#10b981'"
              stroke-width="2"
              opacity="0.6"
              class="npc-glow-ring"
            />
            
            <!-- Larger Main Background Circle -->
            <circle
              cx="0"
              cy="0"
              r="20"
              :fill="npc.color || '#10b981'"
              stroke="#ffffff"
              stroke-width="3"
              class="npc-icon-bg"
              style="filter: url(#npcGlow);"
            />
            
            <!-- Larger High Contrast NPC Person Icon -->
            <g fill="#ffffff" stroke="none" class="npc-person-icon">
              <!-- Head -->
              <circle cx="0" cy="-6" r="5" />
              
              <!-- Body -->
              <rect x="-4" y="1" width="8" height="12" rx="2" />
              
              <!-- Arms -->
              <rect x="-8" y="3" width="3" height="9" rx="1.5" />
              <rect x="5" y="3" width="3" height="9" rx="1.5" />
              
              <!-- Legs -->
              <rect x="-3" y="13" width="2.5" height="8" rx="1.2" />
              <rect x="0.5" y="13" width="2.5" height="8" rx="1.2" />
            </g>
            
            <title>{{ npc.name || 'Unknown NPC' }} ({{ Math.round(npc.x) }}, {{ Math.round(npc.y) }})</title>
          </g>
          
          <!-- NPC Labels -->
          <text
            v-for="npc in npcLocations"
            :key="`label-${npc.id}`"
            :x="npc.x"
            :y="npc.y - npcPinRadius - 5"
            text-anchor="middle"
            class="npc-label"
            :font-size="npcLabelSize"
          >
            {{ npc.name }}
          </text>
        </g>
        
        <!-- Zone Labels -->
        <!-- Zone Labels -->
        <g class="zone-labels">
          <defs>
            <filter id="labelGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
              <feMerge> 
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            
            <filter id="npcGlow" x="-100%" y="-100%" width="300%" height="300%">
              <feGaussianBlur stdDeviation="3" result="npcBlur"/>
              <feFlood flood-color="#10b981" flood-opacity="0.6" result="glowColor"/>
              <feComposite in="glowColor" in2="npcBlur" operator="in" result="coloredGlow"/>
              <feMerge> 
                <feMergeNode in="coloredGlow"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            
            <filter id="npcGlowHover" x="-100%" y="-100%" width="300%" height="300%">
              <feGaussianBlur stdDeviation="4" result="npcBlurHover"/>
              <feFlood flood-color="#10b981" flood-opacity="0.8" result="glowColorHover"/>
              <feComposite in="glowColorHover" in2="npcBlurHover" operator="in" result="coloredGlowHover"/>
              <feMerge> 
                <feMergeNode in="coloredGlowHover"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          
          <!-- Non-portal labels first (background layer) -->
          <template v-for="(label, index) in clusteredLabels.filter(l => l.type !== 'portal' && !l.isPortalCluster)" :key="`bg-label-${index}`">
            <!-- Show as icons/dots when zoomed out -->
            <g v-if="zoomLevel < labelVisibilityThreshold">
              <!-- Invisible larger hover area -->
              <circle
                :cx="label.x"
                :cy="label.y"
                :r="labelDotRadius * 2"
                fill="transparent"
                class="label-hover-area"
                @mouseenter="handleLabelHover(label, $event)"
                @mouseleave="handleLabelLeave"
                @click="handleLabelClick(label, $event)"
              />
            
            <!-- Cluster dot for multiple labels -->
            <g v-if="label.isCluster">
              <!-- Cluster glow effect -->
              <circle
                :cx="label.x"
                :cy="label.y"
                :r="labelDotRadius * 2.2"
                :fill="label.color"
                :opacity="0.3"
                :class="'label-glow'"
                style="pointer-events: none; filter: url(#labelGlow);"
              />
              <!-- Cluster main dot (larger) -->
              <circle
                :cx="label.x"
                :cy="label.y"
                :r="labelDotRadius * 1.3"
                :fill="label.color"
                :opacity="1.0"
                :stroke="'rgba(255, 255, 255, 1.0)'"
                :stroke-width="3"
                :class="['label-dot', { 'hovered': hoveredLabel === label }]"
                style="pointer-events: none;"
              />
              <!-- Cluster count text -->
              <text
                :x="label.x"
                :y="label.y + 4"
                text-anchor="middle"
                :font-size="12"
                fill="white"
                font-weight="bold"
                style="pointer-events: none;"
              >
                {{ label.count }}
              </text>
            </g>
            
            <!-- Regular dot for single labels -->
            <g v-else>
              <!-- Glow effect circle -->
              <circle
                :cx="label.x"
                :cy="label.y"
                :r="labelDotRadius * 1.8"
                :fill="label.color"
                :opacity="0.4"
                :class="'label-glow'"
                style="pointer-events: none; filter: url(#labelGlow);"
              />
              <!-- Main dot -->
              <circle
                :cx="label.x"
                :cy="label.y"
                :r="labelDotRadius"
                :fill="label.color"
                :opacity="1.0"
                :stroke="hoveredLabel === label ? 'rgba(255, 255, 255, 1.0)' : 'rgba(255, 255, 255, 0.8)'"
                :stroke-width="hoveredLabel === label ? 4 : 2"
                :class="['label-dot', { 'hovered': hoveredLabel === label }]"
                style="pointer-events: none;"
              />
            </g>
            </g>
            
            <!-- Show as text when zoomed in -->
            <g v-else>
              <!-- Connecting line if label was separated -->
              <line
                v-if="label.needsConnector"
                :x1="label.originalX"
                :y1="label.originalY"
                :x2="label.displayX"
                :y2="label.displayY"
                :stroke="label.color"
                :stroke-width="1"
                stroke-dasharray="3,4"
                opacity="0.4"
                style="pointer-events: none;"
              />
              
              <!-- Original location dot if label was separated -->
              <circle
                v-if="label.needsConnector"
                :cx="label.originalX"
                :cy="label.originalY"
                :r="3"
                :fill="label.color"
                opacity="0.8"
                style="pointer-events: none;"
              />
              
              <!-- Label text -->
              <text
                :x="label.displayX || label.x"
                :y="label.displayY || label.y"
                :fill="label.color"
                :font-size="labelFontSize"
                text-anchor="middle"
                class="zone-label"
                @mouseenter="handleLabelHover(label, $event)"
                @mouseleave="handleLabelLeave"
                @click="handleLabelClick(label, $event)"
              >
                {{ label.text }}
              </text>
            </g>
          </template>
          
          <!-- Portal labels last (top layer) -->
          <template v-for="(label, index) in clusteredLabels.filter(l => l.type === 'portal' || l.isPortalCluster)" :key="`portal-${index}`">
            <!-- Show as icons/dots when zoomed out -->
            <g v-if="zoomLevel < labelVisibilityThreshold">
              <!-- Invisible larger hover area -->
              <circle
                :cx="label.x"
                :cy="label.y"
                :r="labelDotRadius * 2"
                fill="transparent"
                class="label-hover-area"
                @mouseenter="handleLabelHover(label, $event)"
                @mouseleave="handleLabelLeave"
                @click="handleLabelClick(label, $event)"
              />
              
              <!-- Portal icon for zone exits -->
              <g class="portal-group" style="cursor: pointer;" @click="handleLabelClick(label, $event)">
                <!-- Large white background diamond -->
                <rect
                  :x="label.x - labelDotRadius * 3"
                  :y="label.y - labelDotRadius * 3"
                  :width="labelDotRadius * 6"
                  :height="labelDotRadius * 6"
                  fill="#ffffff"
                  transform="rotate(45)"
                  :transform-origin="`${label.x} ${label.y}`"
                  :opacity="1.0"
                  style="pointer-events: none;"
                />
                <!-- Smaller red diamond inside -->
                <rect
                  :x="label.x - labelDotRadius * 2"
                  :y="label.y - labelDotRadius * 2"
                  :width="labelDotRadius * 4"
                  :height="labelDotRadius * 4"
                  :fill="label.color"
                  transform="rotate(45)"
                  :transform-origin="`${label.x} ${label.y}`"
                  :opacity="1.0"
                  :class="['label-portal', { 'hovered': hoveredLabel === label }]"
                  style="pointer-events: none;"
                />
              </g>
            </g>
            
            <!-- Show as text when zoomed in -->
            <g v-else>
              <!-- Connecting line if label was separated -->
              <line
                v-if="label.needsConnector"
                :x1="label.originalX"
                :y1="label.originalY"
                :x2="label.displayX"
                :y2="label.displayY"
                :stroke="label.color"
                :stroke-width="1"
                stroke-dasharray="3,4"
                opacity="0.4"
                style="pointer-events: none;"
              />
              
              <!-- Original location dot if label was separated -->
              <circle
                v-if="label.needsConnector"
                :cx="label.originalX"
                :cy="label.originalY"
                :r="3"
                :fill="label.color"
                opacity="0.8"
                style="pointer-events: none;"
              />
              
              <!-- Portal text -->
              <text
                :x="label.displayX || label.x"
                :y="label.displayY || label.y"
                :fill="label.color"
                :font-size="labelFontSize"
                text-anchor="middle"
                class="zone-label portal-text"
                font-weight="bold"
                @mouseenter="handleLabelHover(label, $event)"
                @mouseleave="handleLabelLeave"
                @click="handleLabelClick(label, $event)"
                style="cursor: pointer;"
              >
                {{ label.text }}
              </text>
            </g>
          </template>
        </g>
        
        <!-- Grid Lines (optional) -->
        <g v-if="showGrid" class="grid-lines">
          <defs>
            <pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse">
              <path d="M 100 0 L 0 0 0 100" fill="none" stroke="#333" stroke-width="1" opacity="0.3"/>
            </pattern>
          </defs>
          <rect x="0" y="0" width="100%" height="100%" fill="url(#grid)"/>
        </g>
        
        <!-- Dropped Pin -->
        <g v-if="droppedPin" class="dropped-pin">
          <defs>
            <filter id="pinShadow" x="-50%" y="-50%" width="200%" height="200%">
              <feDropShadow dx="2" dy="4" stdDeviation="3" flood-color="rgba(0,0,0,0.3)"/>
            </filter>
          </defs>
          
          <!-- Google Maps style teardrop pin - scaled to be visible -->
          <path
            :d="`M ${droppedPin.x},${droppedPin.y} 
                 C ${droppedPin.x - pinSize},${droppedPin.y - pinSize} 
                   ${droppedPin.x - pinSize},${droppedPin.y - pinSize * 2} 
                   ${droppedPin.x},${droppedPin.y - pinSize * 2}
                 C ${droppedPin.x + pinSize},${droppedPin.y - pinSize * 2} 
                   ${droppedPin.x + pinSize},${droppedPin.y - pinSize} 
                   ${droppedPin.x},${droppedPin.y}
                 Z`"
            fill="#EA4335"
            stroke="#ffffff"
            :stroke-width="pinSize / 15"
            style="pointer-events: none; filter: url(#pinShadow);"
          />
          
          <!-- Pin inner white circle -->
          <circle
            :cx="droppedPin.x"
            :cy="droppedPin.y - pinSize * 1.4"
            :r="pinSize / 3"
            fill="#ffffff"
            style="pointer-events: none;"
          />
        </g>
      </svg>
    </div>
    
    <!-- Label Hover Tooltip -->
    <div 
      v-if="hoveredLabel && zoomLevel < labelVisibilityThreshold"
      class="label-tooltip"
      :style="{ 
        left: hoverPosition.x + 30 + 'px', 
        top: hoverPosition.y - 15 + 'px' 
      }"
    >
      <!-- Single label tooltip -->
      <div v-if="!hoveredLabel.isCluster" class="tooltip-text">{{ hoveredLabel.text }}</div>
      
      <!-- Cluster tooltip with multiple labels -->
      <div v-else class="tooltip-cluster">
        <div class="tooltip-cluster-header">{{ hoveredLabel.count }} Locations</div>
        <div class="tooltip-cluster-items">
          <div 
            v-for="(clusterLabel, index) in hoveredLabel.labels" 
            :key="index"
            class="tooltip-cluster-item"
          >
            {{ clusterLabel.text }}
          </div>
        </div>
      </div>
      
      <div class="tooltip-connector"></div>
    </div>
    
    <!-- Zone Navigation Confirmation Modal -->
    <div v-if="showZoneConfirmation" class="zone-confirmation-overlay" @click="cancelZoneNavigation">
      <div class="zone-confirmation-modal" @click.stop>
        <div class="confirmation-header">
          <h3>Navigate to Zone</h3>
          <button @click="cancelZoneNavigation" class="close-confirmation">×</button>
        </div>
        <div class="confirmation-content">
          <p>Do you want to navigate to <strong>{{ pendingZoneNavigation?.zoneName }}</strong>?</p>
          <div class="confirmation-actions">
            <button @click="cancelZoneNavigation" class="cancel-btn">Cancel</button>
            <button @click="confirmZoneNavigation" class="confirm-btn">Navigate</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Label Legend -->
    <div class="label-legend">
      <div class="legend-title">Map Legend</div>
      <div class="legend-items">
        <div class="legend-item">
          <div class="legend-portal-icon">
            <svg width="16" height="16" viewBox="0 0 16 16">
              <!-- White background diamond -->
              <rect x="4" y="4" width="8" height="8" fill="#ffffff" transform="rotate(45 8 8)"/>
              <!-- Red inner diamond -->
              <rect x="5.5" y="5.5" width="5" height="5" fill="#ff6b6b" transform="rotate(45 8 8)"/>
            </svg>
          </div>
          <span>Zone Exits</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot" style="background-color: #4ecdc4;"></div>
          <span>Travel Points</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot" style="background-color: #ffd93d;"></div>
          <span>NPCs/Creatures</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot" style="background-color: #a78bfa;"></div>
          <span>Buildings</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot" style="background-color: #fb923c;"></div>
          <span>Crafting</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot" style="background-color: #60a5fa;"></div>
          <span>Water</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot" style="background-color: #34d399;"></div>
          <span>Landmarks</span>
        </div>
      </div>
    </div>
    
    <!-- Map Info Panel -->
    <div v-if="selectedNpc" class="map-info-panel">
      <div class="info-header">
        <h4>{{ selectedNpc.name }}</h4>
        <button @click="selectedNpc = null" class="close-info">×</button>
      </div>
      <div class="info-content">
        <p><strong>Level:</strong> {{ selectedNpc.level }}</p>
        <p><strong>Location:</strong> {{ selectedNpc.x }}, {{ selectedNpc.y }}, {{ selectedNpc.z }}</p>
        <p v-if="selectedNpc.race"><strong>Race:</strong> {{ selectedNpc.race }}</p>
        <p v-if="selectedNpc.class"><strong>Class:</strong> {{ selectedNpc.class }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import LoadingModal from './LoadingModal.vue'

export default {
  name: 'ZoneMap',
  components: {
    LoadingModal
  },
  props: {
    zoneData: {
      type: Object,
      required: true
    },
    mapLines: {
      type: Array,
      default: () => []
    },
    mapLabels: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    },
    npcLocations: {
      type: Array,
      default: () => []
    },
    showGrid: {
      type: Boolean,
      default: false
    }
  },
  emits: ['npc-click', 'zone-navigate'],
  setup(props, { emit }) {
    // Refs
    const mapContainer = ref(null)
    const mapSvg = ref(null)
    
    // State
    const zoomLevel = ref(1)
    const panX = ref(0)
    const panY = ref(0)
    const isPanning = ref(false)
    const lastPanPoint = ref({ x: 0, y: 0 })
    const selectedNpc = ref(null)
    const currentCoords = ref(null)
    const showCoordinates = ref(true)
    const hoveredLabel = ref(null)
    const hoverPosition = ref({ x: 0, y: 0 })
    const droppedPin = ref(null) // Stores the dropped pin coordinates
    const isFullscreen = ref(false) // Fullscreen state
    const showZoneConfirmation = ref(false) // Zone navigation confirmation modal
    const pendingZoneNavigation = ref(null) // Stores zone navigation details
    let hoverTimeout = null
    
    // Map bounds
    const mapBounds = ref({ minX: 0, maxX: 1000, minY: 0, maxY: 1000 })
    
    // Computed properties
    const viewBox = computed(() => {
      const bounds = mapBounds.value
      const width = bounds.maxX - bounds.minX
      const height = bounds.maxY - bounds.minY
      
      // Ensure we have reasonable bounds for SVG rendering
      if (width <= 0 || height <= 0 || !isFinite(width) || !isFinite(height)) {
        console.log('Invalid bounds, using default viewBox')
        return "0 0 1000 1000"
      }
      
      const viewBoxStr = `${bounds.minX} ${bounds.minY} ${width} ${height}`
      return viewBoxStr
    })
    
    const processedLines = computed(() => {
      if (!props.mapLines.length) return []
      
      const processed = props.mapLines.map(line => {
        // Check if line starts with 'L ' first
        if (!line.startsWith('L ')) {
          return null
        }
        
        // Split the line by comma-space, but first remove the 'L ' prefix
        const coordsPart = line.substring(2) // Remove 'L '
        const coords = coordsPart.split(', ')
        
        if (coords.length >= 9) {
          const x1 = parseFloat(coords[0])
          const y1 = parseFloat(coords[1]) 
          const z1 = parseFloat(coords[2])
          const x2 = parseFloat(coords[3])
          const y2 = parseFloat(coords[4])
          const z2 = parseFloat(coords[5])
          const r = parseInt(coords[6])
          const g = parseInt(coords[7]) 
          const b = parseInt(coords[8])
          
          // Check if this appears to be a water line
          // Water lines are often dark blue (high blue, low red/green) or specific combinations
          const isWaterLine = (
            (b > r && b > g && b >= 50) || // Blue dominant
            (r === 0 && g === 0 && b > 100) || // Pure blue variants
            (r < 50 && g < 100 && b > 50) || // Bluish combinations
            (r === 0 && g === 0 && b === 255) // Pure bright blue
          )
          
          let brightR, brightG, brightB
          
          if (isWaterLine) {
            // Make water lines bright blue
            brightR = 64   // Darker blue-cyan
            brightG = 164  // Medium cyan
            brightB = 255  // Full blue
          } else {
            // Brighten dark colors for better contrast against dark background
            const brightenColor = (value) => {
              // Handle pure black or very dark colors (0-30) - make them bright white/light gray
              if (value <= 30) {
                return 200 + (value * 2) // Results in 200-260 range, capped at 255
              }
              // If very dark (31-80), brighten significantly
              if (value < 80) {
                return Math.min(255, value + 170)
              }
              // If moderately dark (80-140), brighten moderately
              if (value < 140) {
                return Math.min(255, value + 100)
              }
              // If somewhat dark (140-180), brighten slightly
              if (value < 180) {
                return Math.min(255, value + 50)
              }
              // Otherwise keep original or very slight brightening
              return Math.min(255, value + 10)
            }
            
            brightR = brightenColor(r)
            brightG = brightenColor(g)
            brightB = brightenColor(b)
          }
          
          return {
            x1,
            y1: y1, // Removed Y flip - testing normal orientation
            x2, 
            y2: y2, // Removed Y flip - testing normal orientation
            z1,
            z2,
            color: `rgb(${brightR}, ${brightG}, ${brightB})`,
            width: 25
          }
        }
        return null
      }).filter(line => line !== null)
      
      return processed
    })
    
    const npcPinRadius = computed(() => {
      // Keep this for backward compatibility, though we now use npcIconScale
      const bounds = mapBounds.value
      const viewBoxWidth = bounds.maxX - bounds.minX
      const viewBoxHeight = bounds.maxY - bounds.minY
      const diagonal = Math.sqrt(viewBoxWidth * viewBoxWidth + viewBoxHeight * viewBoxHeight)
      
      const baseSize = diagonal * 0.012 / Math.sqrt(zoomLevel.value)
      return Math.max(6, Math.min(40, baseSize))
    })

    const npcIconScale = computed(() => {
      // DRAMATICALLY larger scale factor for maximum visibility at all zoom levels
      const bounds = mapBounds.value
      const viewBoxWidth = bounds.maxX - bounds.minX
      const viewBoxHeight = bounds.maxY - bounds.minY
      const diagonal = Math.sqrt(viewBoxWidth * viewBoxWidth + viewBoxHeight * viewBoxHeight)
      
      // Much larger base scale - 10x larger than original for extreme visibility
      // Scale inversely with zoom but maintain very high visibility
      const baseScale = diagonal * 0.003 / Math.sqrt(zoomLevel.value)
      
      // Ensure minimum scale of 6.0 and maximum of 15.0 for maximum visibility
      return Math.max(6.0, Math.min(15.0, baseScale))
    })
    
    const npcLabelSize = computed(() => {
      return 14
    })
    
    const mapLineWidth = computed(() => {
      return 2
    })
    
    const processedLabels = computed(() => {
      if (!props.mapLabels.length) return []
      
      const processed = props.mapLabels.map((label, index) => {
        // Check if line starts with 'P ' first
        if (!label.startsWith('P ')) {
          return null
        }
        
        // Split the label by comma-space, but first remove the 'P ' prefix
        const coordsPart = label.substring(2) // Remove 'P '
        const coords = coordsPart.split(', ')
        
        if (coords.length >= 8) {
          const x = parseFloat(coords[0])
          const y = parseFloat(coords[1]) 
          const z = parseFloat(coords[2])
          const r = parseInt(coords[3])
          const g = parseInt(coords[4])
          const b = parseInt(coords[5])
          const size = parseInt(coords[6])
          const text = coords.length > 7 ? coords.slice(7).join(', ').replace(/_/g, ' ') : 'Unknown'
          
          // Validate coordinates
          if (isNaN(x) || isNaN(y) || isNaN(z)) {
            console.log(`Label ${index} rejected - invalid coordinates:`, { x, y, z, raw: label })
            return null
          }
          
          // Categorize labels and assign meaningful colors and types
          const getLabelInfo = (labelText) => {
            const text = labelText.toLowerCase()
            
            // Zone connections (exits/entrances) - use portal icon
            if (text.includes('to ') || text.includes('to_') || text.includes('zone line') || text.includes('zone_line')) {
              return { color: '#ff6b6b', type: 'portal' } // Bright red for zone exits
            }
            
            // Transportation/Travel
            if (text.includes('succor') || text.includes('port') || text.includes('teleport') ||
                text.includes('wizard_spire') || text.includes('druid_ring') || text.includes('stone')) {
              return { color: '#4ecdc4', type: 'dot' } // Bright teal for travel points
            }
            
            // NPCs and Creatures  
            if (text.includes('orc') || text.includes('goblin') || text.includes('skeleton') ||
                text.includes('zombie') || text.includes('undead') || text.includes('bandit') ||
                text.includes('camp') || text.includes('_1') || text.includes('_2') || 
                text.includes('_3') || text.includes('cutthroat') || text.includes('guard')) {
              return { color: '#ffd93d', type: 'dot' } // Bright yellow for NPCs/creatures
            }
            
            // Buildings and Structures
            if (text.includes('inn') || text.includes('tavern') || text.includes('shop') ||
                text.includes('bank') || text.includes('guild') || text.includes('hall') ||
                text.includes('tower') || text.includes('ruins') || text.includes('temple')) {
              return { color: '#a78bfa', type: 'dot' } // Purple for buildings
            }
            
            // Crafting and Utilities
            if (text.includes('forge') || text.includes('kiln') || text.includes('oven') ||
                text.includes('anvil') || text.includes('pottery') || text.includes('gs:')) {
              return { color: '#fb923c', type: 'dot' } // Orange for crafting stations
            }
            
            // Water features
            if (text.includes('water') || text.includes('river') || text.includes('lake') ||
                text.includes('ocean') || text.includes('sea') || text.includes('pool')) {
              return { color: '#60a5fa', type: 'dot' } // Light blue for water features
            }
            
            // Landmarks and Points of Interest
            if (text.includes('landmark') || text.includes('poi') || text.includes('statue') ||
                text.includes('monument') || text.includes('bridge')) {
              return { color: '#34d399', type: 'dot' } // Green for landmarks
            }
            
            // Default fallback - use a neutral but visible color
            return { color: '#f59e0b', type: 'dot' } // Amber/orange for unknown/misc
          }
          
          const labelInfo = getLabelInfo(text)
          
          return {
            x,
            y: y, // Removed Y flip - testing normal orientation
            z,
            color: labelInfo.color,
            type: labelInfo.type,
            originalColor: `rgb(${r}, ${g}, ${b})`, // Keep original for reference
            size: Math.max(2, size),
            text: text.trim()
          }
        } else {
          console.log(`Label ${index} rejected - insufficient coordinates (${coords.length}):`, label)
        }
        return null
      }).filter(label => label !== null)
      
      // Comprehensive validation summary
      const totalRawLabels = props.mapLabels.length
      const totalProcessed = processed.length
      const skipped = totalRawLabels - totalProcessed
      
      // Categorize processed labels
      const categorized = processed.reduce((acc, label) => {
        acc[label.type] = (acc[label.type] || 0) + 1
        return acc
      }, {})
      
      console.log('=== LABEL PROCESSING SUMMARY ===')
      console.log(`Raw labels received: ${totalRawLabels}`)
      console.log(`Successfully processed: ${totalProcessed}`)
      console.log(`Skipped/Invalid: ${skipped}`)
      console.log('Categories:', categorized)
      
      if (categorized.portal) {
        console.log(`✅ Portal labels detected: ${categorized.portal}`)
        const portalLabels = processed.filter(l => l.type === 'portal')
        portalLabels.forEach(p => console.log(`  - ${p.text} at (${Math.round(p.x)}, ${Math.round(-p.y)})`))
      } else {
        console.log('⚠️ No portal labels detected - zone exits may not be visible as portals')
      }
      
      console.log('=================================')
      
      return processed
    })
    
    const labelFontSize = computed(() => {
      // NORMALIZED FONT SIZE: Based on viewport like dots/pins for consistency
      const bounds = mapBounds.value
      const viewBoxWidth = bounds.maxX - bounds.minX
      const viewBoxHeight = bounds.maxY - bounds.minY
      
      // Use percentage of viewport diagonal for consistent readable text
      const diagonal = Math.sqrt(viewBoxWidth * viewBoxWidth + viewBoxHeight * viewBoxHeight)
      const baseSize = diagonal * 0.012 // 1.2% of diagonal - larger than dots for readability
      
      // Counter-scale with zoom to maintain consistent screen size
      const zoomAdjustedSize = baseSize / zoomLevel.value
      
      // Apply bounds for readability - larger minimum than before
      return Math.max(16, Math.min(48, zoomAdjustedSize))
    })
    
    const labelVisibilityThreshold = computed(() => {
      // Labels show text when zoom level is above this threshold
      return 1.5 // Back to original value
    })
    
    const labelDotRadius = computed(() => {
      // TRULY NORMALIZED: Size based on viewport, not map dimensions
      // This ensures consistent visual size regardless of map scale
      const bounds = mapBounds.value
      const viewBoxWidth = bounds.maxX - bounds.minX
      const viewBoxHeight = bounds.maxY - bounds.minY
      
      // Use a fixed percentage of the viewport diagonal for consistency
      const diagonal = Math.sqrt(viewBoxWidth * viewBoxWidth + viewBoxHeight * viewBoxHeight)
      const baseSize = diagonal * 0.006 // 0.6% of diagonal - adjust this for desired size
      
      // Counter-scale with zoom to maintain consistent screen size
      const zoomAdjustedSize = baseSize / zoomLevel.value
      
      // Apply reasonable bounds
      return Math.max(10, Math.min(80, zoomAdjustedSize))
    })
    
    const pinSize = computed(() => {
      // TRULY NORMALIZED: Size based on viewport, not map dimensions  
      // This ensures consistent visual size regardless of map scale
      const bounds = mapBounds.value
      const viewBoxWidth = bounds.maxX - bounds.minX
      const viewBoxHeight = bounds.maxY - bounds.minY
      
      // Use a fixed percentage of the viewport diagonal for consistency
      const diagonal = Math.sqrt(viewBoxWidth * viewBoxWidth + viewBoxHeight * viewBoxHeight)
      const baseSize = diagonal * 0.01 // 1.0% of diagonal - adjust this for desired size
      
      // Counter-scale with zoom level to maintain consistent visual size
      const zoomAdjustedSize = baseSize / zoomLevel.value
      
      // Apply reasonable bounds for usability
      return Math.max(20, Math.min(120, zoomAdjustedSize))
    })
    
    const clusteredLabels = computed(() => {
      if (!processedLabels.value.length) return []
      
      // When zoomed in enough to show text, use smart separation on all labels
      if (zoomLevel.value >= labelVisibilityThreshold.value) {
        return smartSeparateLabels(processedLabels.value)
      }
      
      // Otherwise use clustering for dots - show all labels but cluster them
      const clusters = []
      const processed = new Set()
      
      // Adaptive clustering distance based on zoom level
      const baseClusterDistance = 120
      const clusterDistance = Math.max(50, baseClusterDistance * (2 - zoomLevel.value))
      
      processedLabels.value.forEach((label, index) => {
        if (processed.has(index)) return
        
        const cluster = {
          ...label,
          isCluster: false,
          count: 1,
          labels: [label]
        }
        
        // Find nearby labels - but be more selective about portal clustering
        processedLabels.value.forEach((otherLabel, otherIndex) => {
          if (index === otherIndex || processed.has(otherIndex)) return
          
          // IMPORTANT: Portals should only cluster with other portals to preserve their identity
          if ((label.type === 'portal' && otherLabel.type !== 'portal') ||
              (label.type !== 'portal' && otherLabel.type === 'portal')) {
            return // Skip clustering portals with non-portals
          }
          
          const distance = Math.sqrt(
            Math.pow(label.x - otherLabel.x, 2) + 
            Math.pow(label.y - otherLabel.y, 2)
          )
          
          if (distance <= clusterDistance) {
            cluster.labels.push(otherLabel)
            cluster.count++
            processed.add(otherIndex)
          }
        })
        
        // Mark as cluster if it contains multiple labels
        if (cluster.count > 1) {
          cluster.isCluster = true
          
          // IMPORTANT: Portal dominance - portals should always be the dominant element
          const portalLabels = cluster.labels.filter(l => l.type === 'portal')
          if (portalLabels.length > 0) {
            // Portal is dominant - use portal's properties and position
            const dominantPortal = portalLabels[0] // Use first portal as dominant
            cluster.color = dominantPortal.color
            cluster.type = 'portal'
            cluster.x = dominantPortal.x // Use portal's exact position, not cluster center
            cluster.y = dominantPortal.y
            cluster.text = dominantPortal.text // Use portal's text, not cluster count
            
            // Store portal data for navigation functionality
            cluster.portalData = {
              zoneName: dominantPortal.text,
              originalPortal: dominantPortal
            }
            
            // Mark that this cluster should behave as a portal for click handling
            cluster.isPortalCluster = true
          } else {
            // Use the most common color in the cluster only for non-portal clusters
            const colors = cluster.labels.map(l => l.color)
            const colorCounts = colors.reduce((acc, color) => {
              acc[color] = (acc[color] || 0) + 1
              return acc
            }, {})
            cluster.color = Object.keys(colorCounts).reduce((a, b) => 
              colorCounts[a] > colorCounts[b] ? a : b
            )
            
            // Position cluster at the center of all labels for non-portals
            cluster.x = cluster.labels.reduce((sum, l) => sum + l.x, 0) / cluster.labels.length
            cluster.y = cluster.labels.reduce((sum, l) => sum + l.y, 0) / cluster.labels.length
            cluster.text = `${cluster.count} locations`
            cluster.isPortalCluster = false
          }
        }
        
        clusters.push(cluster)
        processed.add(index)
      })
      
      return clusters
    })
    
    const smartSeparateLabels = (labels) => {
      const fontSize = labelFontSize.value
      const padding = 8 // Extra padding around text
      
      // Calculate more accurate text bounds for each label
      const labelsWithBounds = labels.map(label => {
        // More accurate text width estimation based on character types
        const avgCharWidth = fontSize * 0.55 // Reduced from 0.6
        const textWidth = label.text.length * avgCharWidth + padding * 2
        const textHeight = fontSize + padding * 2
        
        return {
          ...label,
          width: textWidth,
          height: textHeight,
          displayX: label.x,
          displayY: label.y,
          originalX: label.x,
          originalY: label.y,
          needsConnector: false
        }
      })
      
      // Sort labels by importance (shorter text = more important, position near center = more important)
      const centerX = labelsWithBounds.reduce((sum, l) => sum + l.x, 0) / labelsWithBounds.length
      const centerY = labelsWithBounds.reduce((sum, l) => sum + l.y, 0) / labelsWithBounds.length
      
      labelsWithBounds.sort((a, b) => {
        const aPriority = a.text.length + Math.sqrt(Math.pow(a.x - centerX, 2) + Math.pow(a.y - centerY, 2)) / 100
        const bPriority = b.text.length + Math.sqrt(Math.pow(b.x - centerX, 2) + Math.pow(b.y - centerY, 2)) / 100
        return aPriority - bPriority
      })
      
      // Function to check if two labels overlap
      const labelsOverlap = (labelA, labelB) => {
        const left1 = labelA.displayX - labelA.width / 2
        const right1 = labelA.displayX + labelA.width / 2
        const top1 = labelA.displayY - labelA.height / 2
        const bottom1 = labelA.displayY + labelA.height / 2
        
        const left2 = labelB.displayX - labelB.width / 2
        const right2 = labelB.displayX + labelB.width / 2
        const top2 = labelB.displayY - labelB.height / 2
        const bottom2 = labelB.displayY + labelB.height / 2
        
        return !(right1 < left2 || left1 > right2 || bottom1 < top2 || top1 > bottom2)
      }
      
      // Process each label in order of priority
      labelsWithBounds.forEach((currentLabel, currentIndex) => {
        const conflicts = []
        
        // Find all labels that overlap with current label
        labelsWithBounds.forEach((otherLabel, otherIndex) => {
          if (currentIndex === otherIndex) return
          if (labelsOverlap(currentLabel, otherLabel)) {
            conflicts.push(otherLabel)
          }
        })
        
        if (conflicts.length > 0) {
          // Try to find a position that doesn't overlap with any existing labels
          let bestPosition = null
          let bestScore = -1
          
          // Test positions in expanding rings around the original position
          const testRadii = [60, 90, 120, 150, 200]
          const testAngles = [0, Math.PI/4, Math.PI/2, 3*Math.PI/4, Math.PI, 5*Math.PI/4, 3*Math.PI/2, 7*Math.PI/4]
          
          for (const radius of testRadii) {
            for (const angle of testAngles) {
              const testX = currentLabel.originalX + Math.cos(angle) * radius
              const testY = currentLabel.originalY + Math.sin(angle) * radius
              
              // Create test label
              const testLabel = {
                ...currentLabel,
                displayX: testX,
                displayY: testY
              }
              
              // Check if this position overlaps with any other label
              let hasOverlap = false
              let score = 0
              
              labelsWithBounds.forEach((otherLabel, otherIndex) => {
                if (currentIndex === otherIndex) return
                
                if (labelsOverlap(testLabel, otherLabel)) {
                  hasOverlap = true
                  return
                }
                
                // Score based on distance to other labels (prefer more space)
                const dx = testX - otherLabel.displayX
                const dy = testY - otherLabel.displayY
                const distance = Math.sqrt(dx * dx + dy * dy)
                score += distance
              })
              
              // If no overlap and better score, use this position
              if (!hasOverlap && score > bestScore) {
                bestScore = score
                bestPosition = { x: testX, y: testY }
              }
            }
            
            // If we found a good position, stop searching
            if (bestPosition) break
          }
          
          // Apply the best position found
          if (bestPosition) {
            currentLabel.displayX = bestPosition.x
            currentLabel.displayY = bestPosition.y
            
            // Check if we need a connector line
            const distanceFromOriginal = Math.sqrt(
              Math.pow(bestPosition.x - currentLabel.originalX, 2) + 
              Math.pow(bestPosition.y - currentLabel.originalY, 2)
            )
            
            currentLabel.needsConnector = distanceFromOriginal > 30
          } else {
            // If no good position found, use a fallback strategy
            // Place it directly above the original position with enough space
            currentLabel.displayX = currentLabel.originalX
            currentLabel.displayY = currentLabel.originalY - 80
            currentLabel.needsConnector = true
          }
        }
      })
      
      return labelsWithBounds
    }
    
    // Methods
    const calculateMapBounds = () => {
      if (!processedLines.value.length && !processedLabels.value.length) {
        mapBounds.value = { minX: -1000, maxX: 1000, minY: -1000, maxY: 1000 }
        return
      }
      
      let minX = Infinity, maxX = -Infinity
      let minY = Infinity, maxY = -Infinity
      
      // Include map lines in bounds calculation
      processedLines.value.forEach(line => {
        minX = Math.min(minX, line.x1, line.x2)
        maxX = Math.max(maxX, line.x1, line.x2)
        minY = Math.min(minY, line.y1, line.y2)
        maxY = Math.max(maxY, line.y1, line.y2)
      })
      
      // Include labels in bounds calculation
      processedLabels.value.forEach(label => {
        minX = Math.min(minX, label.x)
        maxX = Math.max(maxX, label.x)
        minY = Math.min(minY, label.y)
        maxY = Math.max(maxY, label.y)
      })
      
      // Add padding
      const paddingX = (maxX - minX) * 0.1
      const paddingY = (maxY - minY) * 0.1
      
      mapBounds.value = {
        minX: minX - paddingX,
        maxX: maxX + paddingX,
        minY: minY - paddingY,
        maxY: maxY + paddingY
      }
      
    }
    
    const zoomIn = () => {
      zoomLevel.value = Math.min(zoomLevel.value * 1.2, 20)
    }
    
    const zoomOut = () => {
      zoomLevel.value = Math.max(zoomLevel.value / 1.2, 0.1)
    }
    
    const resetView = async () => {
      console.log('resetView() called - before reset:', {
        zoom: zoomLevel.value,
        panX: panX.value,
        panY: panY.value
      })
      
      zoomLevel.value = 1
      panX.value = 0
      panY.value = 0
      
      // Wait for Vue to update the DOM
      await nextTick()
      
      console.log('resetView() called - after reset and nextTick:', {
        zoom: zoomLevel.value,
        panX: panX.value,
        panY: panY.value
      })
    }
    
    const toggleFullscreen = () => {
      console.log('toggleFullscreen() called, current state:', isFullscreen.value)
      
      if (!isFullscreen.value) {
        console.log('Entering fullscreen...')
        enterFullscreen()
      } else {
        console.log('Exiting fullscreen...')
        exitFullscreen()
        
        // Double-check with a delayed reset as backup
        setTimeout(() => {
          const stillFullscreen = !!(
            document.fullscreenElement ||
            document.webkitFullscreenElement ||
            document.mozFullScreenElement ||
            document.msFullscreenElement
          )
          
          if (!stillFullscreen && isFullscreen.value) {
            console.log('Backup: detected we are no longer fullscreen, forcing reset')
            isFullscreen.value = false
            resetView()
          }
        }, 500)
      }
    }
    
    const enterFullscreen = () => {
      const mapWrapper = mapContainer.value?.closest('.zone-map-wrapper')
      if (mapWrapper && mapWrapper.requestFullscreen) {
        mapWrapper.requestFullscreen().then(() => {
          isFullscreen.value = true
        }).catch((err) => {
          console.error('Failed to enter fullscreen:', err)
        })
      } else if (mapWrapper && mapWrapper.webkitRequestFullscreen) {
        mapWrapper.webkitRequestFullscreen()
        isFullscreen.value = true
      } else if (mapWrapper && mapWrapper.mozRequestFullScreen) {
        mapWrapper.mozRequestFullScreen()
        isFullscreen.value = true
      } else if (mapWrapper && mapWrapper.msRequestFullscreen) {
        mapWrapper.msRequestFullscreen()
        isFullscreen.value = true
      }
    }
    
    const exitFullscreen = () => {
      console.log('exitFullscreen() called, scheduling reset...')
      
      if (document.exitFullscreen) {
        document.exitFullscreen().then(() => {
          isFullscreen.value = false
          // Force reset after exiting fullscreen
          setTimeout(() => {
            console.log('Forcing map reset after exitFullscreen()')
            resetView()
          }, 300)
        }).catch((err) => {
          console.error('Failed to exit fullscreen:', err)
        })
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen()
        isFullscreen.value = false
        setTimeout(() => {
          console.log('Forcing map reset after webkitExitFullscreen()')
          resetView()
        }, 300)
      } else if (document.mozCancelFullScreen) {
        document.mozCancelFullScreen()
        isFullscreen.value = false
        setTimeout(() => {
          console.log('Forcing map reset after mozCancelFullScreen()')
          resetView()
        }, 300)
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen()
        isFullscreen.value = false
        setTimeout(() => {
          console.log('Forcing map reset after msExitFullscreen()')
          resetView()
        }, 300)
      }
    }
    
    const handleFullscreenChange = () => {
      const isCurrentlyFullscreen = !!(
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.mozFullScreenElement ||
        document.msFullscreenElement
      )
      
      console.log('Fullscreen change detected:', {
        wasFullscreen: isFullscreen.value,
        isNowFullscreen: isCurrentlyFullscreen,
        shouldReset: isFullscreen.value && !isCurrentlyFullscreen
      })
      
      // If we're exiting fullscreen, reset the map view with a delay
      if (isFullscreen.value && !isCurrentlyFullscreen) {
        console.log('Exiting fullscreen - scheduling map reset...')
        // Use a longer delay and multiple attempts to ensure DOM has updated
        setTimeout(() => {
          console.log('Executing map reset, current state:', {
            zoom: zoomLevel.value,
            panX: panX.value,
            panY: panY.value
          })
          resetView()
          console.log('Map reset completed, new state:', {
            zoom: zoomLevel.value,
            panX: panX.value,
            panY: panY.value
          })
        }, 200)
      }
      
      isFullscreen.value = isCurrentlyFullscreen
    }
    
    const handleEscapeKey = (event) => {
      if (event.key === 'Escape' && isFullscreen.value) {
        exitFullscreen()
      }
    }
    
    const handleWheel = (event) => {
      event.preventDefault()
      
      if (!mapContainer.value) return
      
      // Get mouse position relative to the map container
      const rect = mapContainer.value.getBoundingClientRect()
      const mouseX = event.clientX - rect.left
      const mouseY = event.clientY - rect.top
      
      // Store the current state
      const oldZoom = zoomLevel.value
      
      // Calculate zoom change
      const delta = event.deltaY > 0 ? 0.9 : 1.1
      const newZoom = Math.max(0.1, Math.min(20, oldZoom * delta))
      
      if (newZoom !== oldZoom) {
        // Calculate the zoom factor
        const zoomRatio = newZoom / oldZoom
        
        // Calculate new pan to keep mouse point stationary
        // The point under the mouse before zoom: (mouseX - panX) / oldZoom, (mouseY - panY) / oldZoom
        // After zoom this point will be at: (mouseX - newPanX) / newZoom, (mouseY - newPanY) / newZoom
        // We want these to be equal, so: (mouseX - panX) / oldZoom = (mouseX - newPanX) / newZoom
        // Solving for newPanX: newPanX = mouseX - (mouseX - panX) * (newZoom / oldZoom)
        
        panX.value = mouseX - (mouseX - panX.value) * zoomRatio
        panY.value = mouseY - (mouseY - panY.value) * zoomRatio
        
        zoomLevel.value = newZoom
      }
    }
    
    const startPan = (event) => {
      if (event.button === 0) { // Left mouse button
        isPanning.value = true
        lastPanPoint.value = { x: event.clientX, y: event.clientY }
      }
    }
    
    const updatePan = (event) => {
      if (isPanning.value) {
        const deltaX = event.clientX - lastPanPoint.value.x
        const deltaY = event.clientY - lastPanPoint.value.y
        
        panX.value += deltaX
        panY.value += deltaY
        
        lastPanPoint.value = { x: event.clientX, y: event.clientY }
      }
    }
    
    const updateCoordinates = (event) => {
      if (!mapContainer.value || !mapSvg.value) return
      
      // Get the SVG element and its bounding box
      const svg = mapSvg.value
      const svgRect = svg.getBoundingClientRect()
      
      // Calculate mouse position relative to SVG viewport
      const mouseX = event.clientX - svgRect.left
      const mouseY = event.clientY - svgRect.top
      
      // Account for the CSS transform applied to the SVG (pan and zoom)
      const unscaledX = mouseX / zoomLevel.value
      const unscaledY = mouseY / zoomLevel.value
      const mapX = unscaledX - panX.value / zoomLevel.value
      const mapY = unscaledY - panY.value / zoomLevel.value
      
      // Convert from SVG pixel coordinates to viewBox coordinates
      const bounds = mapBounds.value
      const viewBoxWidth = bounds.maxX - bounds.minX
      const viewBoxHeight = bounds.maxY - bounds.minY
      
      // Scale to viewBox coordinates
      const svgX = bounds.minX + (mapX / svgRect.width) * viewBoxWidth
      const svgY = bounds.minY + (mapY / svgRect.height) * viewBoxHeight
      
      // Convert to game coordinates for display
      const x = Math.round(svgX)
      const y = Math.round(svgY)
      
      currentCoords.value = { x, y, z: null }
    }
    
    const updatePanAndCoords = (event) => {
      updatePan(event)
      updateCoordinates(event)
    }
    
    const endPan = () => {
      isPanning.value = false
    }
    
    const handleLabelHover = (label, event) => {
      if (!mapContainer.value) return
      
      // Clear any existing timeout
      if (hoverTimeout) {
        clearTimeout(hoverTimeout)
      }
      
      // Get mouse position relative to the map container for stable positioning
      const rect = mapContainer.value.getBoundingClientRect()
      const mouseX = event.clientX - rect.left
      const mouseY = event.clientY - rect.top
      
      // Set tooltip immediately to prevent flickering
      hoveredLabel.value = label
      hoverPosition.value = { x: mouseX, y: mouseY }
    }
    
    const handleLabelLeave = () => {
      // Add delay before hiding to prevent flickering
      hoverTimeout = setTimeout(() => {
        hoveredLabel.value = null
      }, 200)
    }
    
    const handleLabelClick = (label, event) => {
      event.preventDefault()
      event.stopPropagation()
      
      // Handle clicks on portal/zone exit labels (including portal clusters)
      if (label.type === 'portal' || label.isPortalCluster) {
        let zoneName, sourceLabel
        
        if (label.isPortalCluster && label.portalData) {
          // Handle clustered portal - use the dominant portal's data
          zoneName = extractZoneNameFromLabel(label.portalData.zoneName)
          sourceLabel = label.portalData.originalPortal
        } else {
          // Handle individual portal
          zoneName = extractZoneNameFromLabel(label.text)
          sourceLabel = label
        }
        
        if (zoneName) {
          pendingZoneNavigation.value = {
            zoneName: zoneName,
            label: sourceLabel
          }
          showZoneConfirmation.value = true
        }
      }
    }
    
    const extractZoneNameFromLabel = (labelText) => {
      // Extract zone name from various label formats
      const text = labelText.toLowerCase()
      
      // Common patterns for zone exits
      if (text.includes('to ')) {
        const match = text.match(/to\s+(.+)/)
        if (match) return match[1].trim()
      }
      
      if (text.includes('to_')) {
        const match = text.match(/to_(.+)/)
        if (match) return match[1].replace(/_/g, ' ').trim()
      }
      
      if (text.includes('zone line')) {
        // Try to extract zone name from "zone line to X" format
        const match = text.match(/zone\s*line\s*(?:to)?\s*(.+)/)
        if (match) return match[1].trim()
      }
      
      // If it contains zone connection keywords, return the whole text
      if (text.includes('exit') || text.includes('entrance') || text.includes('portal')) {
        return text
      }
      
      return null
    }
    
    const confirmZoneNavigation = () => {
      try {
        if (pendingZoneNavigation.value) {
          // Reset map view (position and zoom) before navigating to new zone
          resetView()
          emit('zone-navigate', pendingZoneNavigation.value.zoneName)
        }
      } catch (error) {
        console.error('Error in confirmZoneNavigation:', error)
      } finally {
        cancelZoneNavigation()
      }
    }
    
    const cancelZoneNavigation = () => {
      showZoneConfirmation.value = false
      pendingZoneNavigation.value = null
    }
    
    const handleDoubleClick = (event) => {
      event.preventDefault()
      
      if (!mapContainer.value) return
      
      // Get mouse position relative to the map container
      const rect = mapContainer.value.getBoundingClientRect()
      const mouseX = event.clientX - rect.left
      const mouseY = event.clientY - rect.top
      
      // Store the current zoom level
      const oldZoom = zoomLevel.value
      
      // Double the zoom level (capped at maximum)
      const newZoom = Math.min(oldZoom * 2, 20)
      
      if (newZoom !== oldZoom) {
        // Calculate the zoom factor
        const zoomRatio = newZoom / oldZoom
        
        // Calculate new pan to center zoom on the clicked point
        // Same logic as mouse wheel zoom but with double-click position
        panX.value = mouseX - (mouseX - panX.value) * zoomRatio
        panY.value = mouseY - (mouseY - panY.value) * zoomRatio
        
        zoomLevel.value = newZoom
      }
    }
    
    const handleRightClick = (event) => {
      event.preventDefault()
      
      if (!mapContainer.value || !mapSvg.value) return
      
      // Get mouse position relative to the map container (not SVG)
      const containerRect = mapContainer.value.getBoundingClientRect()
      const containerX = event.clientX - containerRect.left
      const containerY = event.clientY - containerRect.top
      
      // Account for the CSS transform applied to the SVG: translate(panX, panY) scale(zoomLevel)
      // To reverse this transform:
      // 1. Subtract the translation (panX, panY)
      // 2. Divide by the scale (zoomLevel)
      const transformedX = (containerX - panX.value) / zoomLevel.value
      const transformedY = (containerY - panY.value) / zoomLevel.value
      
      // Now we have coordinates in the original SVG pixel space
      // Convert these to viewBox coordinates, accounting for aspect ratio
      const bounds = mapBounds.value
      const viewBoxWidth = bounds.maxX - bounds.minX
      const viewBoxHeight = bounds.maxY - bounds.minY
      const viewBoxAspectRatio = viewBoxWidth / viewBoxHeight
      
      const containerWidth = mapContainer.value.clientWidth
      const containerHeight = mapContainer.value.clientHeight
      const containerAspectRatio = containerWidth / containerHeight
      
      let svgContentWidth, svgContentHeight, offsetX, offsetY
      
      if (containerAspectRatio > viewBoxAspectRatio) {
        // Container is wider than viewBox - letterboxed horizontally
        svgContentHeight = containerHeight
        svgContentWidth = containerHeight * viewBoxAspectRatio
        offsetX = (containerWidth - svgContentWidth) / 2
        offsetY = 0
      } else {
        // Container is taller than viewBox - letterboxed vertically  
        svgContentWidth = containerWidth
        svgContentHeight = containerWidth / viewBoxAspectRatio
        offsetX = 0
        offsetY = (containerHeight - svgContentHeight) / 2
      }
      
      // Adjust coordinates for letterboxing offset
      const adjustedX = transformedX - offsetX
      const adjustedY = transformedY - offsetY
      
      // Map to viewBox coordinates using actual content area
      const viewBoxX = bounds.minX + (adjustedX / svgContentWidth) * viewBoxWidth
      const viewBoxY = bounds.minY + (adjustedY / svgContentHeight) * viewBoxHeight
      
      // Game coordinates are the same as viewBox coordinates in our system
      const gameX = Math.round(viewBoxX)
      const gameY = Math.round(viewBoxY)
      
      console.log('Pin placement debug (ASPECT RATIO FIXED):', {
        mouseScreen: { x: event.clientX, y: event.clientY },
        containerPos: { x: containerX, y: containerY },
        afterTransform: { x: transformedX, y: transformedY },
        containerSize: { w: containerWidth, h: containerHeight },
        viewBoxSize: { w: viewBoxWidth, h: viewBoxHeight },
        aspectRatios: { container: containerAspectRatio.toFixed(3), viewBox: viewBoxAspectRatio.toFixed(3) },
        svgContentArea: { w: svgContentWidth, h: svgContentHeight },
        letterboxOffset: { x: offsetX, y: offsetY },
        adjustedCoords: { x: adjustedX, y: adjustedY },
        viewBoxCoords: { x: viewBoxX, y: viewBoxY },
        gameCoords: { x: gameX, y: gameY },
        panZoom: { panX: panX.value, panY: panY.value, zoom: zoomLevel.value }
      })
      
      // Set the dropped pin
      droppedPin.value = {
        x: viewBoxX,  // SVG viewBox coordinates for rendering
        y: viewBoxY,
        gameX: gameX, // Game coordinates for display
        gameY: gameY
      }
    }
    
    const clearPin = () => {
      droppedPin.value = null
    }
    
    // Watch for processed lines and labels changes
    watch([processedLines, processedLabels], () => {
      calculateMapBounds()
    }, { immediate: true, flush: 'post' })

    // Watch for NPC locations changes for reactivity
    watch(() => props.npcLocations, (newNpcLocations) => {
      // NPC locations updated - pins will re-render automatically
      if (newNpcLocations.length > 0) {
        console.log(`Plotting ${newNpcLocations.length} NPC spawn locations on map`)
      }
    }, { immediate: true })
    
    // Alternative fullscreen exit detection using window resize
    const handleWindowResize = () => {
      const isCurrentlyFullscreen = !!(
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.mozFullScreenElement ||
        document.msFullscreenElement
      )
      
      // If we think we're fullscreen but the window size suggests otherwise
      if (isFullscreen.value && !isCurrentlyFullscreen) {
        console.log('Window resize detected fullscreen exit')
        setTimeout(() => {
          resetView()
        }, 100)
        isFullscreen.value = false
      }
    }
    
    // Lifecycle
    onMounted(() => {
      calculateMapBounds()
      
      // Add fullscreen event listeners
      document.addEventListener('fullscreenchange', handleFullscreenChange)
      document.addEventListener('webkitfullscreenchange', handleFullscreenChange)
      document.addEventListener('mozfullscreenchange', handleFullscreenChange)
      document.addEventListener('MSFullscreenChange', handleFullscreenChange)
      document.addEventListener('keydown', handleEscapeKey)
      
      // Add window resize listener as backup
      window.addEventListener('resize', handleWindowResize)
    })
    
    onUnmounted(() => {
      // Remove fullscreen event listeners
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
      document.removeEventListener('webkitfullscreenchange', handleFullscreenChange)
      document.removeEventListener('mozfullscreenchange', handleFullscreenChange)
      document.removeEventListener('MSFullscreenChange', handleFullscreenChange)
      document.removeEventListener('keydown', handleEscapeKey)
      window.removeEventListener('resize', handleWindowResize)
    })
    
    return {
      mapContainer,
      mapSvg,
      zoomLevel,
      panX,
      panY,
      isPanning,
      selectedNpc,
      currentCoords,
      showCoordinates,
      hoveredLabel,
      hoverPosition,
      viewBox,
      processedLines,
      processedLabels,
      clusteredLabels,
      npcPinRadius,
      npcIconScale,
      npcLabelSize,
      mapLineWidth,
      labelFontSize,
      labelVisibilityThreshold,
      labelDotRadius,
      pinSize,
      zoomIn,
      zoomOut,
      resetView,
      handleWheel,
      startPan,
      updatePan,
      updateCoordinates,
      updatePanAndCoords,
      endPan,
      handleLabelHover,
      handleLabelLeave,
      handleLabelClick,
      handleDoubleClick,
      handleRightClick,
      clearPin,
      droppedPin,
      isFullscreen,
      toggleFullscreen,
      showZoneConfirmation,
      pendingZoneNavigation,
      confirmZoneNavigation,
      cancelZoneNavigation
    }
  }
}
</script>

<style scoped>
.zone-map-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  background: #1a1a1a;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(139, 92, 246, 0.4);
}

.map-controls {
  position: absolute;
  top: 15px;
  right: 15px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 10;
}

.control-btn {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #4b5563, #374151);
  border: 2px solid #6b7280;
  border-radius: 10px;
  color: #f3f4f6;
  font-size: 20px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5), 0 2px 8px rgba(0, 0, 0, 0.4);
  position: relative;
  backdrop-filter: blur(10px);
}

.control-btn:hover {
  background: linear-gradient(135deg, #6b7280, #4b5563);
  border-color: #9ca3af;
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 8px 20px rgba(139, 92, 246, 0.4), 0 4px 12px rgba(0, 0, 0, 0.5);
  color: #a78bfa;
}

.control-btn:active {
  transform: translateY(-1px) scale(1.02);
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.6), 0 2px 4px rgba(0, 0, 0, 0.4);
}

.zoom-level {
  background: rgba(31, 41, 55, 0.95);
  color: #f3f4f6;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  border: 2px solid rgba(107, 114, 128, 0.6);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5), 0 2px 6px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(12px);
  min-width: 50px;
}

.coordinate-indicator {
  position: absolute;
  top: 15px;
  left: 15px;
  background: rgba(31, 41, 55, 0.95);
  border: 2px solid rgba(107, 114, 128, 0.6);
  border-radius: 12px;
  padding: 8px 12px;
  color: #f3f4f6;
  font-size: 14px;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5), 0 2px 8px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(15px);
  z-index: 10;
  min-width: 120px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.cursor-icon {
  font-size: 16px;
  color: #9ca3af;
  flex-shrink: 0;
}

.pin-coordinate-indicator {
  position: absolute;
  top: 15px;
  left: 200px;
  background: rgba(31, 41, 55, 0.95);
  border: 2px solid rgba(255, 221, 68, 0.6);
  border-radius: 12px;
  padding: 12px 16px;
  color: #f3f4f6;
  font-size: 14px;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5), 0 2px 8px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(15px);
  z-index: 10;
  min-width: 140px;
}

.clear-pin-btn {
  background: rgba(255, 107, 107, 0.2);
  border: 1px solid rgba(255, 107, 107, 0.5);
  color: #ff6b6b;
  padding: 4px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 11px;
  margin-top: 6px;
}

.clear-pin-btn:hover {
  background: rgba(255, 107, 107, 0.3);
  color: #ff8a8a;
}

.coord-label {
  font-size: 11px;
  opacity: 0.8;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: #a78bfa;
  font-weight: 600;
}

.coord-values {
  display: flex;
  gap: 16px;
  font-weight: 700;
}

.coord-axis {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #f9fafb;
}

.map-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
  user-select: none;
  position: relative;
  cursor: crosshair;
}

.map-container:active {
  cursor: grabbing;
}

.map-svg {
  width: 100%;
  height: 100%;
}

.map-lines {
  pointer-events: none;
}

.npc-pins {
  pointer-events: all;
}

/* NPC Pin Base Styles */
.npc-pin {
  cursor: pointer;
  opacity: 1;
  pointer-events: all;
  /* Add initial plot animation */
  animation: npcPlotAnimation 2s ease-out, npcPulse 3s ease-in-out infinite 2s;
}

.npc-pin:hover .npc-icon-bg {
  stroke-width: 3;
  filter: url(#npcGlowHover);
}

.npc-pin:hover .npc-glow-ring {
  opacity: 0.8;
  stroke-width: 2;
}

/* Strong initial plot animation for newly plotted NPCs */
@keyframes npcPlotAnimation {
  0% { 
    opacity: 0;
  }
  10% { 
    opacity: 1;
  }
  15% { 
    opacity: 0.3;
  }
  25% { 
    opacity: 1;
  }
  35% { 
    opacity: 0.4;
  }
  45% { 
    opacity: 1;
  }
  55% { 
    opacity: 0.5;
  }
  65% { 
    opacity: 1;
  }
  75% { 
    opacity: 0.6;
  }
  85% { 
    opacity: 1;
  }
  95% { 
    opacity: 0.8;
  }
  100% { 
    opacity: 1;
  }
}

/* Remove the ongoing pulse - only use for newly plotted NPCs */

/* Individual component styling */
.npc-icon-bg {
  transition: stroke-width 0.3s ease, filter 0.3s ease;
}

.npc-glow-ring {
  transition: opacity 0.3s ease, stroke-width 0.3s ease;
}

.npc-person-icon {
  /* Ensure the icon doesn't interfere with hover detection */
  pointer-events: none;
}

.npc-label {
  fill: #e5e7eb;
  font-weight: bold;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.9);
  pointer-events: none;
  font-family: 'Arial', sans-serif;
}

.zone-labels {
  pointer-events: auto;
}

.zone-label {
  font-weight: 600;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8), -1px -1px 2px rgba(0, 0, 0, 0.8);
  pointer-events: all;
  font-family: 'Arial', sans-serif;
  cursor: pointer;
}

.label-hover-area {
  cursor: pointer;
  pointer-events: all;
}

.label-dot {
  filter: drop-shadow(3px 3px 6px rgba(0, 0, 0, 0.95));
  pointer-events: none;
}

.label-dot.hovered {
  transform: scale(1.05);
  filter: drop-shadow(4px 4px 8px rgba(0, 0, 0, 1.0));
}

.label-portal {
  transition: all 0.2s ease;
  filter: drop-shadow(2px 2px 4px rgba(0, 0, 0, 0.8));
}

.label-portal.hovered {
  transform: scale(1.1);
  filter: drop-shadow(3px 3px 6px rgba(0, 0, 0, 0.9));
}

.label-glow {
  animation: glowPulse 4s ease-in-out infinite;
}

@keyframes glowPulse {
  0% { 
    opacity: 0.3;
  }
  50% { 
    opacity: 0.5;
  }
  100% { 
    opacity: 0.3;
  }
}


.label-tooltip {
  position: absolute;
  pointer-events: none;
  z-index: 1000;
  animation: fadeIn 0.2s ease-in;
}

@keyframes fadeIn {
  from { 
    opacity: 0; 
    transform: translateX(-10px);
  }
  to { 
    opacity: 1; 
    transform: translateX(0);
  }
}

.tooltip-text {
  background: rgba(31, 41, 55, 0.98);
  color: #f3f4f6;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  font-family: 'Arial', sans-serif;
  white-space: nowrap;
  border: 2px solid rgba(139, 92, 246, 0.6);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.6), 0 2px 8px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(12px);
}

.tooltip-cluster {
  background: rgba(31, 41, 55, 0.98);
  color: #f3f4f6;
  padding: 8px 12px;
  border-radius: 8px;
  font-family: 'Arial', sans-serif;
  border: 2px solid rgba(139, 92, 246, 0.6);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.6), 0 2px 8px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(12px);
  max-width: 250px;
}

.tooltip-cluster-header {
  font-size: 14px;
  font-weight: 700;
  color: #a78bfa;
  margin-bottom: 6px;
  border-bottom: 1px solid rgba(107, 114, 128, 0.3);
  padding-bottom: 4px;
}

.tooltip-cluster-items {
  max-height: 200px;
  overflow-y: auto;
}

.tooltip-cluster-item {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 0;
  color: #e5e7eb;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tooltip-cluster-item:not(:last-child) {
  border-bottom: 1px solid rgba(75, 85, 99, 0.2);
  padding-bottom: 4px;
  margin-bottom: 2px;
}

.tooltip-connector {
  position: absolute;
  left: -15px;
  top: 50%;
  transform: translateY(-50%);
  width: 15px;
  height: 2px;
  background: rgba(255, 255, 255, 0.8);
  filter: drop-shadow(1px 1px 2px rgba(0, 0, 0, 0.5));
}

.label-legend {
  position: absolute;
  bottom: 15px;
  right: 15px;
  background: rgba(31, 41, 55, 0.95);
  border: 2px solid rgba(107, 114, 128, 0.6);
  border-radius: 12px;
  padding: 12px 16px;
  backdrop-filter: blur(12px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5), 0 2px 8px rgba(0, 0, 0, 0.3);
  z-index: 10;
  min-width: 140px;
}

.legend-title {
  font-size: 12px;
  font-weight: 700;
  color: #a78bfa;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.legend-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #e5e7eb;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-portal-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.grid-lines {
  pointer-events: none;
  opacity: 0.3;
}

.map-info-panel {
  position: absolute;
  bottom: 10px;
  left: 10px;
  background: rgba(31, 41, 55, 0.95);
  border: 1px solid rgba(75, 85, 99, 0.6);
  border-radius: 8px;
  padding: 1rem;
  min-width: 200px;
  color: #e5e7eb;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  z-index: 10;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(75, 85, 99, 0.5);
}

.info-header h4 {
  margin: 0;
  color: #a78bfa;
  font-size: 1.1rem;
}

.close-info {
  background: none;
  border: none;
  color: #ff6b6b;
  font-size: 18px;
  cursor: pointer;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.info-content p {
  margin: 0.3rem 0;
  font-size: 0.9rem;
}

.info-content strong {
  color: #a78bfa;
}

.btn-icon {
  display: block;
  line-height: 1;
}

.zoom-in-btn:hover .btn-icon {
  transform: scale(1.1);
}

.zoom-out-btn:hover .btn-icon {
  transform: scale(1.1);
}

.reset-btn:hover .btn-icon {
  transform: scale(1.05);
}

/* Add subtle glow effect for better visibility */
.coordinate-indicator {
  box-shadow: 
    0 4px 16px rgba(0, 0, 0, 0.5), 
    0 2px 8px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(167, 139, 250, 0.2);
}

.control-btn {
  box-shadow: 
    0 4px 16px rgba(0, 0, 0, 0.5), 
    0 2px 8px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(107, 114, 128, 0.3);
}

.zoom-level {
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.5), 
    0 2px 6px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(107, 114, 128, 0.2);
}

.fullscreen-btn {
  position: relative;
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #4b5563, #374151);
  border: 2px solid #6b7280;
  border-radius: 10px;
  color: #f3f4f6;
  font-size: 20px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5), 0 2px 8px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(10px);
  z-index: 10;
}

.fullscreen-btn:hover {
  background: linear-gradient(135deg, #6b7280, #4b5563);
  border-color: #9ca3af;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.6), 0 3px 10px rgba(0, 0, 0, 0.5);
}

.fullscreen-btn:active {
  transform: translateY(0px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4), 0 1px 4px rgba(0, 0, 0, 0.3);
}

.fullscreen-icon {
  font-size: 18px;
  line-height: 1;
}

.fullscreen-container {
  position: absolute;
  bottom: 15px;
  left: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 10;
}

.esc-hint {
  background: rgba(31, 41, 55, 0.95);
  border: 1px solid rgba(107, 114, 128, 0.6);
  border-radius: 6px;
  padding: 4px 8px;
  color: #d1d5db;
  font-size: 12px;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
  opacity: 0.8;
  transition: opacity 0.2s ease;
}

.esc-hint:hover {
  opacity: 1;
}

/* Fullscreen styles */
.zone-map-wrapper:fullscreen {
  width: 100vw;
  height: 100vh;
  border-radius: 0;
  border: none;
}

.zone-map-wrapper:-webkit-full-screen {
  width: 100vw;
  height: 100vh;
  border-radius: 0;
  border: none;
}

.zone-map-wrapper:-moz-full-screen {
  width: 100vw;
  height: 100vh;
  border-radius: 0;
  border: none;
}

.zone-map-wrapper:-ms-fullscreen {
  width: 100vw;
  height: 100vh;
  border-radius: 0;
  border: none;
}

/* Zone Navigation Confirmation Modal */
.zone-confirmation-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.zone-confirmation-modal {
  background: linear-gradient(135deg, #1f2937, #111827);
  border: 2px solid rgba(167, 139, 250, 0.5);
  border-radius: 12px;
  padding: 1.5rem;
  max-width: 400px;
  width: 90%;
  color: #e5e7eb;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
}

.confirmation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  border-bottom: 1px solid rgba(75, 85, 99, 0.3);
  padding-bottom: 0.75rem;
}

.confirmation-header h3 {
  margin: 0;
  color: #a78bfa;
  font-size: 1.2rem;
}

.close-confirmation {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.close-confirmation:hover {
  color: #f3f4f6;
  background: rgba(75, 85, 99, 0.3);
}

.confirmation-content p {
  margin: 0 0 1.5rem 0;
  font-size: 1rem;
  line-height: 1.5;
}

.confirmation-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.cancel-btn, .confirm-btn {
  padding: 0.5rem 1.25rem;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-btn {
  background: rgba(75, 85, 99, 0.5);
  color: #d1d5db;
  border: 1px solid rgba(107, 114, 128, 0.5);
}

.cancel-btn:hover {
  background: rgba(75, 85, 99, 0.7);
  color: #f3f4f6;
}

.confirm-btn {
  background: linear-gradient(135deg, #a78bfa, #8b5cf6);
  color: white;
  border: 1px solid rgba(167, 139, 250, 0.8);
}

.confirm-btn:hover {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(167, 139, 250, 0.4);
}

/* Portal text cursor */
.portal-text {
  cursor: pointer;
}

.portal-text:hover {
  filter: brightness(1.2);
}

@media (max-width: 768px) {
  .map-controls {
    top: 10px;
    right: 10px;
    gap: 6px;
  }
  
  .control-btn {
    width: 42px;
    height: 42px;
    font-size: 18px;
  }
  
  .fullscreen-container {
    bottom: 10px;
    left: 10px;
    gap: 6px;
  }
  
  .fullscreen-btn {
    width: 42px;
    height: 42px;
    font-size: 18px;
  }
  
  .esc-hint {
    font-size: 10px;
    padding: 3px 6px;
  }
  
  .coordinate-indicator {
    top: 10px;
    left: 10px;
    padding: 6px 10px;
    font-size: 12px;
    min-width: 100px;
    gap: 6px;
  }
  
  .cursor-icon {
    font-size: 14px;
  }
  
  .coord-values {
    gap: 12px;
  }
  
  .coord-axis {
    font-size: 11px;
  }
  
  .zoom-level {
    padding: 6px 10px;
    font-size: 12px;
  }
  
  .label-legend {
    bottom: 10px;
    right: 10px;
    padding: 10px 12px;
    min-width: 120px;
  }
  
  .legend-title {
    font-size: 11px;
    margin-bottom: 6px;
  }
  
  .legend-items {
    gap: 4px;
  }
  
  .legend-item {
    font-size: 10px;
    gap: 6px;
  }
  
  .legend-dot {
    width: 6px;
    height: 6px;
  }
  
  .map-info-panel {
    left: 5px;
    bottom: 5px;
    min-width: 150px;
    padding: 0.8rem;
  }
  
  .info-header h4 {
    font-size: 1rem;
  }
  
  .info-content p {
    font-size: 0.8rem;
  }
}
</style>