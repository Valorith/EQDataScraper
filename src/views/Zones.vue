<template>
  <div class="zones-container">
    <LoadingModal :visible="loading" text="Loading zones..." />
    
    <div class="zones-header">
      <h1>EverQuest Zones</h1>
      <p>Search and explore zones with interactive maps</p>
    </div>

    <div class="zones-content">
      <!-- Zone Search Section -->
      <div class="zone-search-section">
        <div class="search-container">
          <input 
            v-model="searchQuery" 
            @input="handleSearch"
            @keydown="handleKeydown"
            type="text" 
            placeholder="Search for zones..."
            class="zone-search-input"
          />
          <button 
            v-if="searchQuery.length > 0"
            @click="clearSearch"
            class="search-clear-btn"
            type="button"
            aria-label="Clear search"
          >
            ×
          </button>
          <div v-if="searchResults.length > 0" class="search-results">
            <div 
              v-for="(zone, index) in searchResults" 
              :key="zone.shortName"
              @click="selectZone(zone)"
              @mouseenter="highlightedIndex = index"
              :class="['search-result-item', { 'highlighted': highlightedIndex === index }]"
            >
              <div class="zone-info">
                <div class="zone-name">{{ zone.longName }}</div>
                <div class="zone-short-name">{{ zone.shortName }}</div>
              </div>
              <div class="expansion-icon">
                <img 
                  :src="getExpansionIcon(zone.shortName)" 
                  :alt="getExpansionName(zone.shortName)" 
                  :title="getExpansionName(zone.shortName)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Selected Zone Details -->
      <div v-if="selectedZone" class="selected-zone-section">
        <div class="zone-details-header">
          <h2>{{ selectedZone.longName }}</h2>
          <div class="zone-meta">
            <span class="zone-short">{{ selectedZone.shortName }}</span>
            <button @click="clearSelection" class="clear-btn">Clear Selection</button>
          </div>
        </div>
        
        <!-- Zone Map Component -->
        <div class="zone-map-container">
          <ZoneMap 
            :zoneData="selectedZone"
            :mapLines="mapLines"
            :mapLabels="mapLabels"
            :npcLocations="selectedNpcForMap ? selectedNpcForMap.spawn_locations.map(loc => ({ 
              ...loc, 
              id: selectedNpcForMap.id, 
              name: selectedNpcForMap.full_name.replace(/^#/, '').trim(),
              x: -loc.x,
              y: -loc.y,
              isNewlyPlotted: !!selectedNpcForMap.plotTimestamp
            })) : []"
            :loading="mapLoading"
            @npc-click="handleNpcClick"
            @zone-navigate="handleZoneNavigation"
          />
        </div>
        
        <!-- Zone Information Tabs -->
        <div class="zone-info-tabs">
          <div class="tab-buttons">
            <button 
              v-for="tab in tabs" 
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="['tab-btn', { active: activeTab === tab.id }]"
            >
              {{ tab.name }}
            </button>
          </div>
          
          <div class="tab-content">
            <div v-if="activeTab === 'overview'" class="tab-panel">
              <h3>Zone Overview</h3>
              <p>Detailed information about {{ selectedZone.longName }} will be displayed here.</p>
            </div>
            
            <div v-if="activeTab === 'npcs'" class="tab-panel">
              <div class="npcs-header">
                <h3>NPCs in {{ selectedZone.longName }}</h3>
                <div class="npcs-summary">
                  <button 
                    v-if="selectedNpcForMap" 
                    @click="selectedNpcForMap = null"
                    class="clear-npc-selection-btn"
                    title="Clear map selection"
                  >
                    Clear Map Selection
                  </button>
                  <span v-if="npcsLoading" class="loading-text">Loading NPCs...</span>
                  <span v-else-if="uniqueZoneNpcs.length > 0" class="npc-count">{{ uniqueZoneNpcs.length }} unique NPCs found</span>
                  <span v-else class="no-npcs">No NPCs found</span>
                </div>
              </div>

              <LoadingModal :visible="npcsLoading" text="Loading NPCs..." />

              <div v-if="!npcsLoading && zoneNpcs.length === 0" class="no-npcs-message">
                <div class="no-data-icon">🏰</div>
                <h4>No NPCs Found</h4>
                <p>This zone doesn't have any NPCs in the database, or the database connection is unavailable.</p>
              </div>

              <div v-if="!npcsLoading && zoneNpcs.length > 0" class="npcs-list">
                <div class="npcs-grid">
                  <div 
                    v-for="npc in uniqueZoneNpcs" 
                    :key="npc.id"
                    :class="['npc-card-compact', 'clickable-npc-card', { 'npc-selected': selectedNpcForMap && selectedNpcForMap.id === npc.id }]"
                    @click="openNpcInfo(npc)"
                    :title="`Open ${npc.full_name} details in NPCs page (new tab)`"
                  >
                    <div class="npc-basic-info">
                      <div class="npc-name-compact">
                        {{ npc.full_name }}
                        <span v-if="npc.spawn_count > 1" class="spawn-count-badge">({{ npc.spawn_count }})</span>
                        <i class="fas fa-external-link-alt npc-link-icon"></i>
                      </div>
                      <div class="npc-meta">
                        <span class="npc-level-compact">Lv {{ npc.level }}</span>
                        <span v-if="npc.respawn_time > 0" class="npc-respawn-compact">
                          {{ formatRespawnTime(npc.respawn_time) }}
                        </span>
                        <span v-else class="npc-respawn-compact">Instant</span>
                      </div>
                    </div>
                    
                    <div class="npc-actions">
                      <button 
                        @click="plotNpcOnMap(npc)"
                        class="npc-action-btn map-pin-btn"
                        title="Show on map"
                        style="display: none;"
                        disabled
                      >
                        📍
                      </button>
                      <button 
                        @click.stop="openNpcInfo(npc)"
                        class="npc-action-btn info-btn"
                        title="View details"
                      >
                        ℹ️
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-if="activeTab === 'items'" class="tab-panel">
              <div class="items-header">
                <h3>Items in {{ selectedZone.longName }}</h3>
                <div class="items-summary">
                  <span v-if="itemsLoading" class="loading-text">Loading items...</span>
                  <span v-else-if="uniqueZoneItems.length > 0" class="item-count">{{ uniqueZoneItems.length }} unique items found</span>
                  <span v-else class="no-items">No items found</span>
                </div>
              </div>

              <LoadingModal :visible="itemsLoading" text="Loading items..." />

              <div v-if="!itemsLoading && zoneItems.length === 0" class="no-items-message">
                <div class="no-data-icon">⚔️</div>
                <h4>No Items Found</h4>
                <p>This zone doesn't have any items dropping from NPCs in the database, or the database connection is unavailable.</p>
              </div>

              <div v-if="!itemsLoading && zoneItems.length > 0" class="items-list">
                <!-- Show/Hide All Button -->
                <div class="items-controls">
                  <button 
                    @click.stop="toggleAllGroups"
                    class="toggle-all-btn"
                    :title="allGroupsCollapsed ? 'Expand all item groups' : 'Collapse all item groups'"
                  >
                    <i :class="allGroupsCollapsed ? 'fas fa-chevron-down' : 'fas fa-chevron-up'"></i>
                    {{ allGroupsCollapsed ? 'Show All' : 'Hide All' }}
                  </button>
                </div>

                <div 
                  v-for="group in groupedZoneItems" 
                  :key="group.type"
                  class="item-type-group"
                >
                  <div 
                    class="item-type-header clickable-header"
                    @click.stop="toggleGroup(group.type)"
                    :title="`Click to ${isGroupCollapsed(group.type) ? 'expand' : 'collapse'} ${group.type}`"
                  >
                    <div class="header-content">
                      <i :class="isGroupCollapsed(group.type) ? 'fas fa-chevron-right' : 'fas fa-chevron-down'" class="expand-icon"></i>
                      <h4 class="item-type-title">{{ group.type }}</h4>
                      <span class="item-type-count">({{ group.items.length }})</span>
                    </div>
                  </div>
                  <div 
                    v-if="!isGroupCollapsed(group.type)"
                    class="items-grid"
                  >
                    <div 
                      v-for="item in group.items" 
                      :key="item.id"
                      class="item-card-compact clickable-item"
                      @click="openItemInfo(item)"
                      :title="`Click to view details for ${item.name}`"
                    >
                      <div class="item-icon-container">
                        <img 
                          :src="item.icon_url || '/icons/item_default.png'"
                          :alt="item.name"
                          class="item-icon"
                          @error="handleItemIconError"
                        />
                      </div>
                      <div class="item-basic-info">
                        <div class="item-name-compact">{{ item.name }}</div>
                        <div class="item-meta">
                          <span v-if="item.ac" class="item-stat">AC: {{ item.ac }}</span>
                          <span v-if="item.damage" class="item-stat">DMG: {{ item.damage }}</span>
                          <span v-if="item.delay" class="item-stat">DLY: {{ item.delay }}</span>
                          <span v-if="item.drop_count > 1" class="drop-count-badge">({{ item.drop_count }})</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-if="activeTab === 'quests'" class="tab-panel">
              <h3>Quests</h3>
              <p>Quest information for this zone.</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Default State -->
      <div v-else class="no-zone-selected">
        <div class="zone-placeholder">
          <!-- Treasure Map SVG -->
          <div class="treasure-map">
            <svg width="350" height="240" viewBox="0 0 350 240" xmlns="http://www.w3.org/2000/svg">
              <!-- Parchment background -->
              <defs>
                <filter id="parchmentShadow" x="-30%" y="-30%" width="160%" height="160%">
                  <feDropShadow dx="0" dy="8" stdDeviation="4" flood-color="rgba(0,0,0,0.4)"/>
                  <feDropShadow dx="0" dy="15" stdDeviation="8" flood-color="rgba(0,0,0,0.2)"/>
                </filter>
                
                <pattern id="parchmentTexture" patternUnits="userSpaceOnUse" width="4" height="4">
                  <rect width="4" height="4" fill="#f4e4bc"/>
                  <circle cx="1" cy="1" r="0.5" fill="#e6d5a8" opacity="0.5"/>
                  <circle cx="3" cy="3" r="0.3" fill="#d4c297" opacity="0.3"/>
                </pattern>
                
                <!-- Gradients for 3D effect -->
                <linearGradient id="mapGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#f8f0d6;stop-opacity:1" />
                  <stop offset="30%" style="stop-color:#f4e4bc;stop-opacity:1" />
                  <stop offset="70%" style="stop-color:#e6d5a8;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#d4c297;stop-opacity:1" />
                </linearGradient>
                
                <linearGradient id="leftRollGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" style="stop-color:#c4b286;stop-opacity:1" />
                  <stop offset="30%" style="stop-color:#d4c297;stop-opacity:1" />
                  <stop offset="70%" style="stop-color:#e6d5a8;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#f4e4bc;stop-opacity:0.8" />
                </linearGradient>
                
                <linearGradient id="rightRollGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" style="stop-color:#f4e4bc;stop-opacity:0.8" />
                  <stop offset="30%" style="stop-color:#e6d5a8;stop-opacity:1" />
                  <stop offset="70%" style="stop-color:#d4c297;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#c4b286;stop-opacity:1" />
                </linearGradient>
                
                <radialGradient id="rollHighlight" cx="50%" cy="20%" r="80%">
                  <stop offset="0%" style="stop-color:#fff;stop-opacity:0.3" />
                  <stop offset="100%" style="stop-color:#fff;stop-opacity:0" />
                </radialGradient>
              </defs>
              
              <!-- Left rolled edge -->
              <path d="M15 40 Q25 35 30 45 Q32 120 30 195 Q25 205 15 200 Q18 120 15 40 Z" 
                    fill="url(#leftRollGradient)" 
                    stroke="#b8a582" 
                    stroke-width="1"/>
              
              <!-- Right rolled edge -->
              <path d="M335 40 Q325 35 320 45 Q318 120 320 195 Q325 205 335 200 Q332 120 335 40 Z" 
                    fill="url(#rightRollGradient)" 
                    stroke="#b8a582" 
                    stroke-width="1"/>
              
              <!-- Main parchment map background with perspective -->
              <path d="M30 45 Q175 25 320 45 L320 195 Q175 215 30 195 Z" 
                    fill="url(#mapGradient)" 
                    stroke="#d4c297" 
                    stroke-width="2"
                    style="filter: url(#parchmentShadow);"/>
              
              <!-- Highlight overlay for 3D effect -->
              <path d="M30 45 Q175 25 320 45 L320 195 Q175 215 30 195 Z" 
                    fill="url(#rollHighlight)" 
                    opacity="0.4"/>
              
              <!-- Torn edges effect for 3D perspective -->
              <path d="M40 50 Q45 45 50 50 Q55 55 60 50 Q65 45 70 50" 
                    fill="none" stroke="#d4c297" stroke-width="1" opacity="0.6"/>
              <path d="M280 185 Q285 180 290 185 Q295 190 300 185 Q305 180 310 185" 
                    fill="none" stroke="#d4c297" stroke-width="1" opacity="0.6"/>
              
              <!-- Dotted path following the 3D curve -->
              <path d="M60 70 Q85 80 125 75 Q155 73 185 80 Q220 87 260 90 Q285 92 300 95" 
                    fill="none" 
                    stroke="#8b4513" 
                    stroke-width="3" 
                    stroke-dasharray="8,6" 
                    stroke-linecap="round"
                    opacity="0.8"/>
              
              <!-- Path decorative dots -->
              <circle cx="60" cy="70" r="3" fill="#8b4513" opacity="0.8"/>
              <circle cx="110" cy="77" r="2" fill="#8b4513" opacity="0.6"/>
              <circle cx="160" cy="80" r="2" fill="#8b4513" opacity="0.6"/>
              <circle cx="210" cy="87" r="2" fill="#8b4513" opacity="0.6"/>
              
              <!-- Treasure X mark -->
              <g transform="translate(295, 93)">
                <circle cx="0" cy="0" r="12" fill="#dc2626" opacity="0.2"/>
                <path d="M-8 -8 L8 8 M8 -8 L-8 8" 
                      stroke="#dc2626" 
                      stroke-width="4" 
                      stroke-linecap="round"/>
              </g>
              
              <!-- Compass rose -->
              <g transform="translate(55, 170)" opacity="0.7">
                <circle cx="0" cy="0" r="15" fill="#8b4513" opacity="0.1"/>
                <path d="M0 -12 L3 -6 L0 -3 L-3 -6 Z" fill="#dc2626"/>
                <path d="M0 12 L3 6 L0 3 L-3 6 Z" fill="#8b4513"/>
                <path d="M12 0 L6 3 L3 0 L6 -3 Z" fill="#8b4513"/>
                <path d="M-12 0 L-6 3 L-3 0 L-6 -3 Z" fill="#8b4513"/>
                <text x="0" y="-18" text-anchor="middle" font-size="8" fill="#8b4513" font-weight="bold">N</text>
              </g>
              
              <!-- Mountain ranges -->
              <g opacity="0.4">
                <path d="M85 60 L90 50 L95 60 L100 55 L105 60 L110 52 L115 60" 
                      fill="none" stroke="#8b4513" stroke-width="2"/>
                <path d="M200 65 L205 55 L210 65 L215 58 L220 65 L225 57 L230 65" 
                      fill="none" stroke="#8b4513" stroke-width="2"/>
              </g>
              
              <!-- Trees -->
              <g opacity="0.5">
                <circle cx="130" cy="55" r="4" fill="#228b22"/>
                <rect x="128" y="55" width="4" height="8" fill="#8b4513"/>
                <circle cx="190" cy="135" r="4" fill="#228b22"/>
                <rect x="188" y="135" width="4" height="8" fill="#8b4513"/>
                <circle cx="170" cy="65" r="3" fill="#228b22"/>
                <rect x="168.5" y="65" width="3" height="6" fill="#8b4513"/>
              </g>
              
              <!-- Water/river flowing with perspective -->
              <path d="M45 120 Q65 115 85 120 Q105 125 125 120 Q145 115 165 120 Q185 123 205 120 Q225 118 245 120" 
                    fill="none" 
                    stroke="#4682b4" 
                    stroke-width="6" 
                    opacity="0.6"/>
              <path d="M47 122 Q67 117 87 122 Q107 127 127 122 Q147 117 167 122 Q187 125 207 122 Q227 120 247 122" 
                    fill="none" 
                    stroke="#87ceeb" 
                    stroke-width="2" 
                    opacity="0.8"/>
              
              <!-- Creases and folds for realism -->
              <path d="M50 50 Q175 30 300 50" 
                    fill="none" 
                    stroke="#e6d5a8" 
                    stroke-width="0.5" 
                    opacity="0.3"/>
              <path d="M50 190 Q175 210 300 190" 
                    fill="none" 
                    stroke="#d4c297" 
                    stroke-width="0.5" 
                    opacity="0.4"/>
            </svg>
          </div>
          
          <h3>No Zone Selected</h3>
          <p>Search for and select a zone to view its interactive map and details</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import LoadingModal from '../components/LoadingModal.vue'
import ZoneMap from '../components/ZoneMap.vue'
import { useBackendUrl } from '../composables/useBackendUrl'
import axios from 'axios'

export default {
  name: 'Zones',
  components: {
    LoadingModal,
    ZoneMap
  },
  setup() {
    const { backendUrl } = useBackendUrl()
    const router = useRouter()
    const route = useRoute()
    
    // Reactive state
    const loading = ref(false)
    const mapLoading = ref(false)
    const searchQuery = ref('')
    const searchResults = ref([])
    const highlightedIndex = ref(-1)
    const selectedZone = ref(null)
    const mapLines = ref([])
    const mapLabels = ref([])
    const activeTab = ref('overview')
    const isSettingSearchQuery = ref(false) // Flag to prevent auto-search when setting query programmatically
    const zoneNpcs = ref([])
    const npcsLoading = ref(false)
    const selectedNpcForMap = ref(null)
    const zoneItems = ref([])
    const itemsLoading = ref(false)
    const collapsedGroups = ref([])  // Track which groups are collapsed
    const allGroupsCollapsed = ref(true)    // Track if all groups are collapsed
    
    // Available zones list - comprehensive list including variations
    const availableZones = ref([
      // Classic Zones
      { shortName: 'akanon', longName: 'Akanon' },
      { shortName: 'befallen', longName: 'Befallen' },
      { shortName: 'befallenb', longName: 'Befallen (Lower)' },
      { shortName: 'blackburrow', longName: 'Blackburrow' },
      { shortName: 'crushbone', longName: 'Crushbone' },
      { shortName: 'everfrost', longName: 'Everfrost Peaks' },
      { shortName: 'feerrott', longName: 'The Feerrott' },
      { shortName: 'gfaydark', longName: 'Greater Faydark' },
      { shortName: 'lfaydark', longName: 'Lesser Faydark' },
      { shortName: 'halas', longName: 'Halas' },
      { shortName: 'highkeep', longName: 'High Keep' },
      { shortName: 'highpass', longName: 'Highpass Hold' },
      { shortName: 'kithicor', longName: 'Kithicor Forest' },
      { shortName: 'lavastorm', longName: 'Lavastorm Mountains' },
      { shortName: 'mistmoore', longName: 'Castle Mistmoore' },
      { shortName: 'najena', longName: 'Najena' },
      { shortName: 'nektulos', longName: 'Nektulos Forest' },
      { shortName: 'oasis', longName: 'Oasis of Marr' },
      { shortName: 'southro', longName: 'South Desert of Ro' },
      { shortName: 'northro', longName: 'North Desert of Ro' },
      { shortName: 'eastdesert', longName: 'East Desert of Ro' },
      { shortName: 'rivervale', longName: 'Rivervale' },
      { shortName: 'unrest', longName: 'Estate of Unrest' },
      { shortName: 'paw', longName: 'Lair of the Splitpaw' },
      { shortName: 'permafrost', longName: 'Permafrost Keep' },
      { shortName: 'runnyeye', longName: 'Clan RunnyEye' },
      { shortName: 'soldunga', longName: 'Solusek\'s Eye' },
      { shortName: 'soldungb', longName: 'Nagafen\'s Lair' },
      { shortName: 'kedge', longName: 'Kedge Keep' },
      { shortName: 'paineel', longName: 'Paineel' },
      { shortName: 'hole', longName: 'The Hole' },
      { shortName: 'guk', longName: 'City of Guk' },
      { shortName: 'guktop', longName: 'Upper Guk' },
      { shortName: 'gukbottom', longName: 'Lower Guk' },
      { shortName: 'guka', longName: 'Guk A' },
      { shortName: 'gukb', longName: 'Guk B' },
      { shortName: 'gukc', longName: 'Guk C' },
      { shortName: 'gukd', longName: 'Guk D' },
      { shortName: 'guke', longName: 'Guk E' },
      { shortName: 'gukf', longName: 'Guk F' },
      { shortName: 'gukg', longName: 'Guk G' },
      { shortName: 'gukh', longName: 'Guk H' },
      { shortName: 'erudnext', longName: 'Erudin' },
      { shortName: 'erudnint', longName: 'Erudin Palace' },
      { shortName: 'tox', longName: 'Toxxulia Forest' },
      { shortName: 'neriaka', longName: 'Neriak Foreign Quarter' },
      { shortName: 'neriakb', longName: 'Neriak Commons' },
      { shortName: 'neriakc', longName: 'Neriak Third Gate' },
      { shortName: 'commons', longName: 'The Commonlands' },
      { shortName: 'commonlands', longName: 'The Commonlands' },
      { shortName: 'eastcommons', longName: 'East Commonlands' },
      { shortName: 'westcommons', longName: 'West Commonlands' },
      { shortName: 'steamfont', longName: 'Steamfont Mountains' },
      { shortName: 'lakerathe', longName: 'Lake Rathetear' },
      { shortName: 'rathemtn', longName: 'Rathe Mountains' },
      { shortName: 'innothule', longName: 'Innothule Swamp' },
      
      // Cities and Main Areas
      { shortName: 'qeynos', longName: 'North Qeynos' },
      { shortName: 'qeynos2', longName: 'South Qeynos' },
      { shortName: 'qcat', longName: 'Qeynos Catacombs' },
      { shortName: 'freporte', longName: 'East Freeport' },
      { shortName: 'freportn', longName: 'North Freeport' },
      { shortName: 'freportw', longName: 'West Freeport' },
      { shortName: 'kaladima', longName: 'North Kaladim' },
      { shortName: 'kaladimb', longName: 'South Kaladim' },
      { shortName: 'felwithea', longName: 'Northern Felwithe' },
      { shortName: 'felwitheb', longName: 'Southern Felwithe' },
      { shortName: 'grobb', longName: 'Grobb' },
      { shortName: 'oggok', longName: 'Oggok' },
      { shortName: 'cabeast', longName: 'Cabilis East' },
      { shortName: 'cabwest', longName: 'Cabilis West' },
      
      // Karanas
      { shortName: 'qey2hh1', longName: 'West Karana' },
      { shortName: 'northkarana', longName: 'North Karana' },
      { shortName: 'southkarana', longName: 'South Karana' },
      { shortName: 'eastkarana', longName: 'East Karana' },
      
      // Common Outdoor Zones
      { shortName: 'commonlands', longName: 'Commonlands' },
      { shortName: 'commons', longName: 'West Commonlands' },
      { shortName: 'ecommons', longName: 'East Commonlands' },
      { shortName: 'butcher', longName: 'Butcherblock Mountains' },
      { shortName: 'cauldron', longName: 'Dagnor\'s Cauldron' },
      { shortName: 'lakerathe', longName: 'Lake Rathetear' },
      { shortName: 'innothule', longName: 'Innothule Swamp' },
      { shortName: 'rathemtn', longName: 'Rathe Mountains' },
      { shortName: 'beholder', longName: 'Gorge of King Xorbb' },
      { shortName: 'misty', longName: 'Misty Thicket' },
      { shortName: 'steamfont', longName: 'Steamfont Mountains' },
      { shortName: 'oot', longName: 'Ocean of Tears' },
      { shortName: 'erudsxing', longName: 'Erud\'s Crossing' },
      { shortName: 'stonebrunt', longName: 'Stonebrunt Mountains' },
      { shortName: 'warrens', longName: 'The Warrens' },
      { shortName: 'toxxulia', longName: 'Toxxulia Forest' },
      { shortName: 'kerraridge', longName: 'Kerra Isle' },
      { shortName: 'tutorial', longName: 'Tutorial Zone' },
      { shortName: 'load', longName: 'Loading' },
      { shortName: 'load2', longName: 'Loading' },
      
      // Kunark Zones
      { shortName: 'emeraldjungle', longName: 'Emerald Jungle' },
      { shortName: 'firiona', longName: 'Firiona Vie' },
      { shortName: 'overthere', longName: 'The Overthere' },
      { shortName: 'fieldofbone', longName: 'Field of Bone' },
      { shortName: 'kurn', longName: 'Kurn\'s Tower' },
      { shortName: 'kurntower', longName: 'Kurn\'s Tower' },
      { shortName: 'warslikswood', longName: 'Warsliks Woods' },
      { shortName: 'warsliks', longName: 'Warsliks Woods' },
      { shortName: 'dreadlands', longName: 'Dreadlands' },
      { shortName: 'burningwood', longName: 'Burning Woods' },
      { shortName: 'burning', longName: 'Burning Woods' },
      { shortName: 'skyfire', longName: 'Skyfire Mountains' },
      { shortName: 'frontier', longName: 'Frontier Mountains' },
      { shortName: 'lakeofillomen', longName: 'Lake of Ill Omen' },
      { shortName: 'lakeillomen', longName: 'Lake of Ill Omen' },
      { shortName: 'swampofnohope', longName: 'Swamp of No Hope' },
      { shortName: 'swampnohope', longName: 'Swamp of No Hope' },
      { shortName: 'trakanon', longName: 'Trakanon\'s Teeth' },
      { shortName: 'timorous', longName: 'Timorous Deep' },
      { shortName: 'chardok', longName: 'Chardok' },
      { shortName: 'chardokb', longName: 'Halls of Betrayal' },
      { shortName: 'droga', longName: 'Temple of Droga' },
      { shortName: 'nurga', longName: 'Mines of Nurga' },
      { shortName: 'kaesora', longName: 'Kaesora' },
      { shortName: 'sebilis', longName: 'Old Sebilis' },
      { shortName: 'oldsebilis', longName: 'Old Sebilis' },
      { shortName: 'citymist', longName: 'City of Mist' },
      { shortName: 'karnor', longName: 'Karnor\'s Castle' },
      { shortName: 'karnors', longName: 'Karnor\'s Castle' },
      { shortName: 'veeshanspe', longName: 'Veeshan\'s Peak' },
      { shortName: 'vp', longName: 'Veeshan\'s Peak' },
      { shortName: 'howlingstones', longName: 'Howling Stones' },
      { shortName: 'charasis', longName: 'Howling Stones' },
      
      // Velious Zones
      { shortName: 'eastwastes', longName: 'Eastern Wastes' },
      { shortName: 'iceclad', longName: 'Iceclad Ocean' },
      { shortName: 'cobaltscar', longName: 'Cobalt Scar' },
      { shortName: 'greatdivide', longName: 'Great Divide' },
      { shortName: 'wakening', longName: 'Wakening Land' },
      { shortName: 'wakeningland', longName: 'Wakening Land' },
      { shortName: 'westwastes', longName: 'Western Wastes' },
      { shortName: 'crystal', longName: 'Crystal Caverns' },
      { shortName: 'crystalcaverns', longName: 'Crystal Caverns' },
      { shortName: 'frozenshadow', longName: 'Tower of Frozen Shadow' },
      { shortName: 'necropolis', longName: 'Dragon Necropolis' },
      { shortName: 'dragnecro', longName: 'Dragon Necropolis' },
      
      // High Priority Missing Zones (from test analysis)
      { shortName: 'poknowledge', longName: 'Plane of Knowledge' },
      { shortName: 'potranquility', longName: 'Plane of Tranquility' },
      { shortName: 'lfaydark', longName: 'Lesser Faydark' },
      { shortName: 'eastwastes', longName: 'Eastern Wastes' },
      { shortName: 'fieldofscale', longName: 'Field of Scale' },
      { shortName: 'potime', longName: 'Plane of Time' },
      { shortName: 'iceclad', longName: 'Iceclad Ocean' },
      { shortName: 'shardslanding', longName: 'Shard\'s Landing' },
      { shortName: 'sepulcher', longName: 'Sepulcher of Order' },
      { shortName: 'frontier', longName: 'Frontier Mountains' },
      { shortName: 'overthere', longName: 'The Overthere' },
      { shortName: 'oceangreen', longName: 'Oceangreen Hills' },
      { shortName: 'soldungb', longName: 'Nagafen\'s Lair' },
      { shortName: 'dragonscale', longName: 'Dragonscale Hills' },
      { shortName: 'barindu', longName: 'Barindu, Hanging Gardens' },
      { shortName: 'westwastes', longName: 'Western Wastes' },
      { shortName: 'thevoid', longName: 'The Void' },
      { shortName: 'dranik', longName: 'The Ruined City of Dranik' },
      { shortName: 'fieldofbone', longName: 'The Field of Bone' },
      { shortName: 'broodlands', longName: 'The Broodlands' },
      { shortName: 'stoneroot', longName: 'Stoneroot Falls' },
      { shortName: 'soldunga', longName: 'Solusek\'s Eye' },
      { shortName: 'provinggrounds', longName: 'Muramite Proving Grounds' },
      { shortName: 'kithicor', longName: 'Bloody Kithicor' },
      { shortName: 'warslikswood', longName: 'The Warsliks Woods' },
      { shortName: 'swampofnohope', longName: 'The Swamp of No Hope' },
      { shortName: 'greatdivide', longName: 'The Great Divide' },
      { shortName: 'lakerathetear', longName: 'Lake Rathetear' },
      { shortName: 'bazaar', longName: 'The Bazaar' },
      { shortName: 'nexus', longName: 'The Nexus' },
      { shortName: 'shadowhaven', longName: 'Shadow Haven' },
      
      // Additional missing zones from second wave analysis
      { shortName: 'paineel', longName: 'Paineel' },
      { shortName: 'lakeofillomen', longName: 'Lake of Ill Omen' },
      { shortName: 'firiona', longName: 'Firiona Vie' },
      { shortName: 'cobaltscar', longName: 'Cobalt Scar' },
      { shortName: 'dreadlands', longName: 'The Dreadlands' },
      { shortName: 'chardok', longName: 'Chardok' },
      { shortName: 'cabeast', longName: 'Cabilis East' },
      { shortName: 'cabwest', longName: 'Cabilis West' },
      { shortName: 'timorous', longName: 'Timorous Deep' },
      { shortName: 'droga', longName: 'The Temple of Droga' },
      { shortName: 'echocaverns', longName: 'Echo Caverns' },
      { shortName: 'grimling', longName: 'Grimling Forest' },
      { shortName: 'dulak', longName: 'Dulak\'s Harbor' },
      { shortName: 'gunthak', longName: 'The Gulf of Gunthak' },
      { shortName: 'torgiran', longName: 'Torgiran Mines' },
      { shortName: 'nadox', longName: 'Crypt of Nadox' },
      { shortName: 'hatesfury', longName: 'Hate\'s Fury, The Scorched Woods' },
      { shortName: 'bloodfields', longName: 'Old Bloodfields' },
      { shortName: 'oldbloodfields', longName: 'Old Bloodfields' },
      { shortName: 'lopingplains', longName: 'Loping Plains' },
      { shortName: 'draniksscar', longName: 'Dranik\'s Scar' },
      { shortName: 'causeway', longName: 'The Causeway' },
      { shortName: 'undershore', longName: 'The Undershore' },
      { shortName: 'buried', longName: 'The Buried Sea' },
      { shortName: 'buriedsea', longName: 'The Buried Sea' },
      { shortName: 'solteris', longName: 'Solteris, the Throne of Ro' },
      { shortName: 'devastation', longName: 'Devastation' },
      { shortName: 'ruins', longName: 'Ruins of Illsalin' },
      { shortName: 'illsalin', longName: 'Ruins of Illsalin' },
      
      // Modern expansion zones (post-PoP era)
      { shortName: 'shardslanding', longName: 'Shard\'s Landing' },
      { shortName: 'housethule', longName: 'House of Thule' },
      { shortName: 'scorchedwoods', longName: 'The Scorched Woods' },
      { shortName: 'resplendenttemple', longName: 'The Resplendent Temple' },
      { shortName: 'sarith', longName: 'Sarith, City of Tides' },
      { shortName: 'qinimi', longName: 'Qinimi, Court of Nihilia' },
      { shortName: 'kattacastrum', longName: 'Katta Castrum' },
      { shortName: 'freeportsewers', longName: 'Freeport Sewers' },
      { shortName: 'drunder', longName: 'Drunder, the Fortress of Zek' },
      { shortName: 'underquarry', longName: 'The Underquarry' },
      { shortName: 'toskirakk', longName: 'Toskirakk' },
      { shortName: 'laurioninn', longName: 'Laurion Inn' },
      { shortName: 'korafax', longName: 'Korafax, Home of the Riders' },
      { shortName: 'mechanotus', longName: 'Fortress Mechanotus' },
      { shortName: 'ethernerekarana', longName: 'Ethernere Tainted West Karana' },
      { shortName: 'brellsrest', longName: 'Brell\'s Rest' },
      { shortName: 'hive', longName: 'The Hive' },
      { shortName: 'templeveeshan', longName: 'Temple of Veeshan' },
      { shortName: 'kael', longName: 'Kael Drakkel' },
      { shortName: 'kaeldrakkel', longName: 'Kael Drakkel' },
      { shortName: 'skyshrine', longName: 'Skyshrine' },
      { shortName: 'thurgadina', longName: 'Thurgadin' },
      { shortName: 'thurgadin', longName: 'Thurgadin' },
      { shortName: 'thurgadinb', longName: 'Icewell Keep' },
      { shortName: 'icewell', longName: 'Icewell Keep' },
      { shortName: 'growthplane', longName: 'Plane of Growth' },
      { shortName: 'mischiefplane', longName: 'Plane of Mischief' },
      { shortName: 'sleeper', longName: 'Sleeper\'s Tomb' },
      { shortName: 'sleepers', longName: 'Sleeper\'s Tomb' },
      { shortName: 'sleeperstomb', longName: 'Sleeper\'s Tomb' },
      { shortName: 'sirens', longName: 'Siren\'s Grotto' },
      { shortName: 'sirensgrotto', longName: 'Siren\'s Grotto' },
      
      // Planes
      { shortName: 'airplane', longName: 'Plane of Sky' },
      { shortName: 'fearplane', longName: 'Plane of Fear' },
      { shortName: 'hateplane', longName: 'Plane of Hate' },
      { shortName: 'hateplaneb', longName: 'Plane of Hate B' },
      
      // Shadows of Luclin Zones
      { shortName: 'shadowhaven', longName: 'Shadow Haven' },
      { shortName: 'nexus', longName: 'The Nexus' },
      { shortName: 'sharvahl', longName: 'Shar Vahl' },
      { shortName: 'netherbian', longName: 'Netherbian Lair' },
      { shortName: 'ssratemple', longName: 'Ssraeshza Temple' },
      { shortName: 'griegsend', longName: 'Grieg\'s End' },
      { shortName: 'vexthal', longName: 'Vex Thal' },
      { shortName: 'luclin', longName: 'Luclin' },
      { shortName: 'umbral', longName: 'Umbral Plains' },
      { shortName: 'scarlet', longName: 'Scarlet Desert' },
      { shortName: 'tenebrous', longName: 'Tenebrous Mountains' },
      { shortName: 'twilight', longName: 'Twilight Sea' },
      { shortName: 'grimling', longName: 'Grimling Forest' },
      { shortName: 'mseru', longName: 'Marus Seru' },
      { shortName: 'sseru', longName: 'Sanctus Seru' },
      { shortName: 'akheva', longName: 'Akheva Ruins' },
      { shortName: 'maiden', longName: 'Maiden\'s Eye' },
      { shortName: 'dawnshroud', longName: 'Dawnshroud Peaks' },
      { shortName: 'echo', longName: 'Echo Caverns' },
      { shortName: 'fungusgrove', longName: 'Fungus Grove' },
      { shortName: 'hollowshade', longName: 'Hollowshade Moor' },
      { shortName: 'paludal', longName: 'Paludal Caverns' },
      { shortName: 'katta', longName: 'Katta Castellum' },
      
      // Planes of Power Zones
      { shortName: 'pojustice', longName: 'Plane of Justice' },
      { shortName: 'potranquility', longName: 'Plane of Tranquility' },
      { shortName: 'bothunder', longName: 'Bastion of Thunder' },
      { shortName: 'postorms', longName: 'Plane of Storms' },
      { shortName: 'hohonora', longName: 'Halls of Honor' },
      { shortName: 'hohonorb', longName: 'Temple of Marr' },
      { shortName: 'solrotower', longName: 'Solusek Ro\'s Tower' },
      { shortName: 'potimea', longName: 'Plane of Time A' },
      { shortName: 'potimeb', longName: 'Plane of Time B' },
      { shortName: 'codecay', longName: 'Crypt of Decay' },
      { shortName: 'ponightmare', longName: 'Plane of Nightmare' },
      { shortName: 'podisease', longName: 'Plane of Disease' },
      { shortName: 'poinnovation', longName: 'Plane of Innovation' },
      { shortName: 'potorment', longName: 'Plane of Torment' },
      { shortName: 'povalor', longName: 'Plane of Valor' },
      { shortName: 'fireplane', longName: 'Doomfire, The Burning Lands' },
      { shortName: 'powater', longName: 'Plane of Water' },
      { shortName: 'poair', longName: 'Plane of Air' },
      { shortName: 'poeartha', longName: 'Plane of Earth A' },
      { shortName: 'poearthb', longName: 'Plane of Earth B' },
      { shortName: 'pofire', longName: 'Plane of Fire' },
      
      // Legacy of Ykesha Zones
      { shortName: 'gunthak', longName: 'Gulf of Gunthak' },
      { shortName: 'nadox', longName: 'Crypt of Nadox' },
      { shortName: 'yxtta', longName: 'Yxtta, Pulpit of Exiles' },
      { shortName: 'uqua', longName: 'Uqua, The Ocean God Chantry' },
      { shortName: 'kodtaz', longName: 'Kod\'Taz, Broken Trial Grounds' },
      { shortName: 'ikkinz', longName: 'Ikkinz, Chambers of Righteousness' },
      { shortName: 'qinimi', longName: 'Qinimi, Court of Nihilia' },
      { shortName: 'riwwi', longName: 'Riwwi, Coliseum of Games' },
      { shortName: 'barindu', longName: 'Barindu, Hanging Gardens' },
      { shortName: 'ferubi', longName: 'Ferubi, Forgotten Temple of Taelosia' },
      { shortName: 'snpool', longName: 'Sewers of Nihilia, Pool of Sludge' },
      { shortName: 'snlair', longName: 'Sewers of Nihilia, Lair of Trapped Ones' },
      { shortName: 'snplant', longName: 'Sewers of Nihilia, Purifying Plant' },
      { shortName: 'sncrematory', longName: 'Sewers of Nihilia, the Crematory' },
      { shortName: 'tipt', longName: 'Tipt, Treacherous Crags' },
      { shortName: 'vxed', longName: 'Vxed, The Crumbling Caverns' },
      { shortName: 'abysmal', longName: 'Abysmal Sea' },
      { shortName: 'natimbi', longName: 'Natimbi, the Fallen City' },
      { shortName: 'taelosia', longName: 'Taelosia, The Seed of Life' },
      
      // Dragons of Norrath Zones
      { shortName: 'broodlands', longName: 'The Broodlands' },
      { shortName: 'stillmoona', longName: 'Stillmoon Temple' },
      { shortName: 'stillmoonb', longName: 'The Ascent' },
      { shortName: 'thundercrest', longName: 'Thundercrest Isles' },
      { shortName: 'lavaspire', longName: 'Lavaspire\'s Lair' },
      { shortName: 'tirranun', longName: 'Tirranun\'s Delve' },
      { shortName: 'provinggrounds', longName: 'The Proving Grounds' },
      { shortName: 'delvea', longName: 'Lavastorm Mountains' },
      { shortName: 'delveb', longName: 'The Delve' },
      { shortName: 'thenest', longName: 'The Nest' },
      { shortName: 'ruined', longName: 'The Ruined City of Dranik' },
      { shortName: 'bloodfields', longName: 'The Bloodfields' },
      { shortName: 'causeway', longName: 'Nobles\' Causeway' },
      { shortName: 'draniksscar', longName: 'Dranik\'s Scar' },
      { shortName: 'wallofslaughter', longName: 'Wall of Slaughter' }
    ])
    
    // Expansion mapping data
    const expansionMapping = {
      // Classic Zones
      'classic': ['akanon', 'befallen', 'befallenb', 'blackburrow', 'crushbone', 'everfrost', 'feerrott', 
                  'gfaydark', 'lfaydark', 'halas', 'highkeep', 'highpass', 'kithicor', 'lavastorm', 
                  'mistmoore', 'najena', 'nektulos', 'oasis', 'southro', 'northro', 'eastdesert', 
                  'rivervale', 'unrest', 'paw', 'permafrost', 'runnyeye', 'soldunga', 'soldungb', 
                  'kedge', 'paineel', 'hole', 'guk', 'guktop', 'gukbottom', 'guka', 'gukb', 'gukc', 
                  'gukd', 'guke', 'gukf', 'gukg', 'gukh', 'erudnext', 'erudnint', 'tox', 'toxxulia', 'neriaka', 
                  'neriakb', 'neriakc', 'commons', 'commonlands', 'eastcommons', 'westcommons', 
                  'steamfont', 'lakerathe', 'rathemtn', 'innothule', 'qeynos', 'qeynos2', 'qcat', 
                  'freporte', 'freportn', 'freportw', 'kaladima', 'kaladimb', 'felwithea', 'felwitheb', 
                  'grobb', 'oggok', 'qey2hh1', 'northkarana', 'southkarana', 'eastkarana', 'ecommons', 
                  'butcher', 'cauldron', 'beholder', 'misty', 'mistythicket', 'oot', 'oceanoftears', 
                  'erudsxing', 'stonebrunt', 'warrens', 'kerraridge', 'tutorial', 'tutoriala', 'tutorialb',
                  'load', 'load2', 'airplane', 'fearplane', 'hateplane', 'hateplaneb', 'cazicthule', 'xorbb'],
      
      // Ruins of Kunark
      'kunark': ['emeraldjungle', 'firiona', 'overthere', 'fieldofbone', 'kurn', 'kurntower', 
                 'warslikswood', 'warsliks', 'dreadlands', 'burningwood', 'burning', 'skyfire', 
                 'frontier', 'frontiermtns', 'frontiermtnsb', 'lakeofillomen', 'lakeillomen', 'swampofnohope', 'swampnohope', 
                 'trakanon', 'timorous', 'timorousfalls', 'chardok', 'chardokb', 'chardoktwo', 'droga', 'drogab', 'nurga', 'kaesora', 
                 'sebilis', 'oldsebilis', 'citymist', 'karnor', 'karnors', 'veeshanspe', 'vp', 'veeshan', 
                 'howlingstones', 'charasis', 'charasisb', 'charasistwo', 'cabeast', 'cabwest', 'dalnir', 'veksar'],
      
      // Scars of Velious  
      'velious': ['eastwastes', 'eastwastestwo', 'eastwastesshard', 'iceclad', 'cobaltscar', 'cobaltscartwo', 
                  'greatdivide', 'greatdividetwo', 'wakening', 'wakeningland', 'westwastes', 'westwastestwo', 
                  'crystal', 'crystalcaverns', 'crystaltwoa', 'crystaltwob', 'frozenshadow', 'frozenshadowtwo', 
                  'necropolis', 'necropolistwo', 'dragnecro', 'kael', 'kaeldrakkel', 'kaelshard', 'kaeltwo', 
                  'skyshrine', 'skyshrinetwo', 'thurgadina', 'thurgadin', 'thurgadinb', 'icewell', 
                  'velketor', 'velketortwo', 'growthplane', 'mischiefplane', 'sleeper', 'sleepers', 'sleeperstomb', 'sleepertwo', 
                  'sirens', 'sirensgrotto', 'templeveeshan', 'templeveeshantwo', 'icefall', 'frostcrypt'],
      
      // Shadows of Luclin
      'luclin': ['shadowhaven', 'nexus', 'sharvahl', 'netherbian', 'ssratemple', 'griegsend', 
                 'vexthal', 'luclin', 'umbral', 'scarlet', 'tenebrous', 'twilight', 'grimling', 
                 'mseru', 'sseru', 'akheva', 'maiden', 'dawnshroud', 'echo', 'echocaverns', 
                 'fungusgrove', 'hollowshade', 'paludal', 'katta', 'bazaar'],
      
      // Planes of Power
      'pop': ['poknowledge', 'potranquility', 'pojustice', 'bothunder', 'postorms', 'hohonora', 
              'hohonorb', 'solrotower', 'potimea', 'potimeb', 'potime', 'codecay', 'ponightmare', 
              'podisease', 'poinnovation', 'potorment', 'povalor', 'fireplane', 'powater', 'poair', 
              'poeartha', 'poearthb', 'pofire'],
      
      // Legacy of Ykesha
      'ykesha': ['gunthak', 'dulak'],
      
      // Gates of Discord  
      'god': ['abysmal', 'natimbi', 'qinimi', 'barindu', 'ferubi', 'snpool', 'snlair', 'snplant', 
              'sncrematory', 'tipt', 'vxed', 'nadox', 'yxtta', 'uqua', 'kodtaz', 'ikkinz', 'riwwi', 
              'taelosia'],
      
      // Omens of War
      'oow': ['wallofslaughter', 'bloodfields', 'oldbloodfields', 'causeway', 'draniksscar', 'ruined'],
      
      // Dragons of Norrath
      'don': ['broodlands', 'stillmoona', 'stillmoonb', 'thundercrest', 'lavaspire', 'tirranun', 
              'provinggrounds', 'delvea', 'delveb', 'thenest'],
      
      // Modern Expansions (simplified grouping)
      'modern': ['shardslanding', 'housethule', 'scorchedwoods', 'resplendenttemple', 'sarith', 
                 'kattacastrum', 'freeportsewers', 'drunder', 'underquarry', 'toskirakk', 
                 'laurioninn', 'korafax', 'mechanotus', 'ethernerekarana', 'brellsrest', 'hive', 
                 'fieldofscale', 'sepulcher', 'oceangreen', 'dragonscale', 'thevoid', 'dranik', 
                 'stoneroot', 'lopingplains', 'undershore', 'buried', 'buriedsea', 'solteris', 
                 'devastation', 'ruins', 'illsalin', 'hatesfury', 'torgiran']
    }
    
    // Expansion display names and icons
    const expansionInfo = {
      'classic': { name: 'Classic EverQuest', icon: '/expansions/original.gif' },
      'kunark': { name: 'Ruins of Kunark', icon: '/expansions/kunarkicon.gif' },
      'velious': { name: 'Scars of Velious', icon: '/expansions/veliousicon.gif' },
      'luclin': { name: 'Shadows of Luclin', icon: '/expansions/luclinicon.gif' },
      'pop': { name: 'Planes of Power', icon: '/expansions/poricon.png' },
      'ykesha': { name: 'Legacy of Ykesha', icon: '/expansions/original.gif' },
      'god': { name: 'Gates of Discord', icon: '/expansions/gatesicon.gif' },
      'oow': { name: 'Omens of War', icon: '/expansions/omensicon.gif' },
      'don': { name: 'Dragons of Norrath', icon: '/expansions/dodicon.png' },
      'modern': { name: 'Modern Expansions', icon: '/expansions/secrets.gif' }
    }
    
    // Helper functions for expansion mapping
    const getExpansionForZone = (zoneShortName) => {
      for (const [expansion, zones] of Object.entries(expansionMapping)) {
        if (zones.includes(zoneShortName.toLowerCase())) {
          return expansion
        }
      }
      return 'modern' // Default to modern for unknown zones
    }
    
    const getExpansionName = (zoneShortName) => {
      const expansion = getExpansionForZone(zoneShortName)
      return expansionInfo[expansion]?.name || 'Modern Expansions'
    }
    
    const getExpansionIcon = (zoneShortName) => {
      const expansion = getExpansionForZone(zoneShortName)
      return expansionInfo[expansion]?.icon || '/expansions/secrets.gif'
    }
    
    // Tab configuration
    const tabs = ref([
      { id: 'overview', name: 'Overview' },
      { id: 'npcs', name: 'NPCs' },
      { id: 'items', name: 'Items' },
      { id: 'quests', name: 'Quests' }
    ])
    
    // Computed properties
    const filteredZones = computed(() => {
      if (!searchQuery.value.trim()) return []
      const query = searchQuery.value.toLowerCase()
      return availableZones.value.filter(zone => 
        zone.longName.toLowerCase().includes(query) ||
        zone.shortName.toLowerCase().includes(query)
      )
    })

    // Group NPCs by name - combine NPCs with same name and aggregate all spawn locations
    const uniqueZoneNpcs = computed(() => {
      const npcMap = new Map()
      
      // Helper function to check if name should be filtered out
      const shouldFilterOut = (name) => {
        const cleanName = name.replace(/^#/, '').trim()
        
        // Filter out NPCs that don't have at least one letter (case-insensitive)
        const hasLetter = /[a-zA-Z]/.test(cleanName)
        const isEmpty = cleanName === ''
        
        return !hasLetter || isEmpty
      }
      
      zoneNpcs.value.forEach(npc => {
        // Skip NPCs with filtered names
        if (shouldFilterOut(npc.full_name)) {
          return
        }
        
        const cleanName = npc.full_name.replace(/^#/, '').trim()
        const key = cleanName.toLowerCase() // Use cleaned name as unique identifier
        
        if (!npcMap.has(key)) {
          // First occurrence - create entry with spawn locations array
          npcMap.set(key, {
            ...npc,
            full_name: cleanName,
            name: npc.name.replace(/^#/, '').trim(),
            spawn_locations: [{
              x: npc.location.x,
              y: npc.location.y,
              z: npc.location.z,
              heading: npc.location.heading,
              respawn_time: npc.spawn_info.respawn_time,
              spawn_chance: npc.spawn_info.spawn_chance
            }],
            respawn_time: npc.spawn_info.respawn_time, // Primary respawn time
            spawn_count: 1 // Track how many spawn locations this NPC has
          })
        } else {
          // Additional spawn location for same named NPC
          const existing = npcMap.get(key)
          existing.spawn_locations.push({
            x: npc.location.x,
            y: npc.location.y,
            z: npc.location.z,
            heading: npc.location.heading,
            respawn_time: npc.spawn_info.respawn_time,
            spawn_chance: npc.spawn_info.spawn_chance
          })
          existing.spawn_count += 1
          
          // Use the shortest respawn time among all instances
          if (npc.spawn_info.respawn_time < existing.respawn_time) {
            existing.respawn_time = npc.spawn_info.respawn_time
          }
        }
      })
      
      return Array.from(npcMap.values()).sort((a, b) => {
        // Sort by level descending, then by name
        if (a.level !== b.level) return b.level - a.level
        return a.full_name.localeCompare(b.full_name)
      })
    })

    // Group items by ID - combine items with same ID and count occurrences
    const uniqueZoneItems = computed(() => {
      const itemMap = new Map()
      
      zoneItems.value.forEach(item => {
        const key = item.id // Use item ID as unique identifier
        
        if (!itemMap.has(key)) {
          // First occurrence - create entry
          itemMap.set(key, {
            ...item,
            drop_count: 1, // Track how many NPCs drop this item
            icon_url: item.icon ? `/icons/items/${item.icon}.png` : null
          })
        } else {
          // Additional occurrence - increment count
          const existing = itemMap.get(key)
          existing.drop_count += 1
        }
      })
      
      return Array.from(itemMap.values()).sort((a, b) => {
        // Sort by name alphabetically
        return a.name.localeCompare(b.name)
      })
    })

    // Group items by item type
    const groupedZoneItems = computed(() => {
      const groups = new Map()
      
      uniqueZoneItems.value.forEach(item => {
        const itemType = getItemTypeDisplay(item.item_type)
        
        if (!groups.has(itemType)) {
          groups.set(itemType, [])
        }
        groups.get(itemType).push(item)
      })
      
      // Convert to array and sort groups by type name
      const groupedArray = Array.from(groups.entries()).map(([type, items]) => ({
        type,
        items: items.sort((a, b) => a.name.localeCompare(b.name)) // Sort items within each group
      }))
      
      // Sort groups by type name
      const sortedGroups = groupedArray.sort((a, b) => a.type.localeCompare(b.type))
      
      return sortedGroups
    })
    
    // Collapse/expand functions
    const toggleGroup = (groupType) => {
      console.log('toggleGroup called for:', groupType)
      const index = collapsedGroups.value.indexOf(groupType)
      if (index > -1) {
        console.log('Expanding group:', groupType)
        collapsedGroups.value.splice(index, 1)
      } else {
        console.log('Collapsing group:', groupType)
        collapsedGroups.value.push(groupType)
      }
      updateAllGroupsState()
      console.log('Current collapsed groups:', collapsedGroups.value)
    }
    
    const toggleAllGroups = () => {
      console.log('toggleAllGroups called, current state:', allGroupsCollapsed.value)
      if (allGroupsCollapsed.value) {
        // Expand all
        console.log('Expanding all groups')
        collapsedGroups.value.length = 0
        allGroupsCollapsed.value = false
      } else {
        // Collapse all
        console.log('Collapsing all groups')
        collapsedGroups.value = groupedZoneItems.value.map(group => group.type)
        allGroupsCollapsed.value = true
      }
      console.log('After toggle, collapsed groups:', collapsedGroups.value)
    }
    
    const updateAllGroupsState = () => {
      const totalGroups = groupedZoneItems.value.length
      const collapsedCount = collapsedGroups.value.length
      allGroupsCollapsed.value = collapsedCount === totalGroups
    }
    
    const isGroupCollapsed = (groupType) => {
      return collapsedGroups.value.includes(groupType)
    }
    
    
    // Methods
    const handleSearch = () => {
      if (searchQuery.value.trim().length >= 1) {
        searchResults.value = filteredZones.value.slice(0, 10)
        highlightedIndex.value = 0 // Auto-highlight first result
      } else {
        searchResults.value = []
        highlightedIndex.value = -1
      }
    }
    
    const selectZone = async (zone) => {
      loading.value = true
      mapLoading.value = true
      searchResults.value = []
      highlightedIndex.value = -1
      searchQuery.value = ''
      zoneNpcs.value = []
      zoneItems.value = []
      
      try {
        selectedZone.value = zone
        // Load map data, NPCs, and items in parallel
        await Promise.all([
          loadZoneMap(zone.shortName),
          loadZoneNpcs(zone.shortName),
          loadZoneItems(zone.shortName)
        ])
      } catch (error) {
        console.error('Error selecting zone:', error)
      } finally {
        loading.value = false
        mapLoading.value = false
      }
    }
    
    const loadZoneNpcs = async (zoneShortName) => {
      try {
        npcsLoading.value = true
        const url = `${backendUrl.value}/api/zone-npcs/${zoneShortName}`
        console.log('Fetching NPCs from:', url)
        
        const response = await fetch(url)
        if (!response.ok) {
          if (response.status === 503) {
            console.warn('Database not connected for NPC data')
            zoneNpcs.value = []
            return
          }
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        console.log('NPC data received:', data)
        
        zoneNpcs.value = data.npcs || []
      } catch (error) {
        console.error('Error loading zone NPCs:', error)
        zoneNpcs.value = []
      } finally {
        npcsLoading.value = false
      }
    }
    
    const loadZoneMap = async (zoneShortName) => {
      try {
        const url = `${backendUrl.value}/api/zone-map/${zoneShortName}`
        const response = await axios.get(url)
        mapLines.value = response.data.lines || []
        mapLabels.value = response.data.labels || []
        console.log(`Loaded ${mapLines.value.length} lines and ${mapLabels.value.length} labels for ${zoneShortName}`)
      } catch (error) {
        console.error('Error loading zone map:', error)
        mapLines.value = []
        mapLabels.value = []
      }
    }

    const loadZoneItems = async (zoneShortName) => {
      itemsLoading.value = true
      try {
        const url = `${backendUrl.value}/api/zone-items/${zoneShortName}`
        console.log('Fetching zone items from:', url)
        
        const response = await fetch(url)
        if (!response.ok) {
          if (response.status === 503) {
            console.warn('Database not connected for item data')
            zoneItems.value = []
            return
          }
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        console.log('Item data received:', data)
        
        zoneItems.value = data.items || []
      } catch (error) {
        console.error('Error loading zone items:', error)
        zoneItems.value = []
      } finally {
        itemsLoading.value = false
      }
    }
    
    const clearSelection = () => {
      selectedZone.value = null
      mapLines.value = []
      mapLabels.value = []
      zoneNpcs.value = []
      zoneItems.value = []
      selectedNpcForMap.value = null
      searchQuery.value = ''
      searchResults.value = []
      activeTab.value = 'overview'
    }
    
    const handleNpcClick = (npcData) => {
      console.log('NPC clicked:', npcData)
      // TODO: Show detailed NPC information modal or navigate to NPC details
    }

    const plotNpcOnMap = (npc) => {
      console.log('Plotting NPC on map:', npc.full_name, 'Locations:', npc.spawn_locations)
      
      // Set the selected NPC for the map to display
      selectedNpcForMap.value = {
        ...npc,
        plotTimestamp: Date.now() // Add timestamp to trigger animation
      }
      
      // Scroll to map section for better UX
      const mapContainer = document.querySelector('.zone-map-container')
      if (mapContainer) {
        mapContainer.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
      
      // After 1 second, reduce the size by clearing the newly plotted flag
      setTimeout(() => {
        if (selectedNpcForMap.value && selectedNpcForMap.value.plotTimestamp) {
          selectedNpcForMap.value = {
            ...selectedNpcForMap.value,
            plotTimestamp: null
          }
        }
      }, 1000) // Size reduction after 1 second
    }

    const openNpcInfo = async (npc) => {
      try {
        // Open NPC details page in new tab with auto-open modal parameter
        // The NPCs page expects 'npc' parameter with the NPC ID
        const npcUrl = `${window.location.origin}/npcs?npc=${npc.id}`
        
        // Open in new tab
        window.open(npcUrl, '_blank', 'noopener,noreferrer')
      } catch (error) {
        console.error('Error opening NPC details:', error)
      }
    }
    
    const formatRespawnTime = (seconds) => {
      if (seconds <= 0) return 'Instant'
      if (seconds < 60) return `${seconds}s`
      if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
      if (seconds < 86400) {
        const hours = Math.floor(seconds / 3600)
        const minutes = Math.floor((seconds % 3600) / 60)
        return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`
      }
      const days = Math.floor(seconds / 86400)
      const hours = Math.floor((seconds % 86400) / 3600)
      return hours > 0 ? `${days}d ${hours}h` : `${days}d`
    }

    const handleItemIconError = (event) => {
      // Fallback to default item icon if loading fails
      event.target.src = '/icons/item_default.png'
    }

    const openItemInfo = async (item) => {
      try {
        // Open Item details page in new tab with auto-open modal parameter
        // The Items page expects 'item' parameter with the item ID  
        const itemUrl = `/items?item=${item.id}`
        
        // Open in new tab
        window.open(itemUrl, '_blank')
      } catch (error) {
        console.error('Error opening item details:', error)
      }
    }
    
    const handleZoneNavigation = (zoneName) => {
      // Find matching zone in the available zones list
      const matchedZone = availableZones.value.find(zone => {
        // Try exact match first
        if (zone.shortName.toLowerCase() === zoneName.toLowerCase() || 
            zone.longName.toLowerCase() === zoneName.toLowerCase()) {
          return true
        }
        
        // Try partial matches for common abbreviations and variations
        const zoneNameLower = zoneName.toLowerCase()
        const shortNameLower = zone.shortName.toLowerCase()
        const longNameLower = zone.longName.toLowerCase()
        
        // Handle common variations
        if (zoneNameLower.includes('steamfont') && shortNameLower.includes('steamfont')) return true
        if (zoneNameLower.includes('mountains') && longNameLower.includes('mountains')) return true
        if (zoneNameLower.includes('forest') && longNameLower.includes('forest')) return true
        if (zoneNameLower.includes('desert') && longNameLower.includes('desert')) return true
        
        // Handle Desert of Ro variations
        if (zoneNameLower.includes('south') && zoneNameLower.includes('desert') && zoneNameLower.includes('ro')) {
          return shortNameLower === 'southro'
        }
        if (zoneNameLower.includes('north') && zoneNameLower.includes('desert') && zoneNameLower.includes('ro')) {
          return shortNameLower === 'northro'
        }
        if (zoneNameLower.includes('east') && zoneNameLower.includes('desert') && zoneNameLower.includes('ro')) {
          return shortNameLower === 'eastdesert'
        }
        
        // Handle City of Guk variations
        if ((zoneNameLower.includes('city') && zoneNameLower.includes('guk')) || 
            zoneNameLower.includes('the city of guk')) {
          return shortNameLower === 'guk'
        }
        
        // Handle Upper/Lower Guk variations
        if (zoneNameLower.includes('upper') && zoneNameLower.includes('guk')) {
          return shortNameLower === 'guktop'
        }
        if (zoneNameLower.includes('lower') && zoneNameLower.includes('guk')) {
          return shortNameLower === 'gukbottom'
        }
        
        // Handle "Ruins of Old Guk" variations
        if ((zoneNameLower.includes('ruins') && zoneNameLower.includes('old') && zoneNameLower.includes('guk')) ||
            (zoneNameLower.includes('ruins') && zoneNameLower.includes('guk'))) {
          return shortNameLower === 'gukbottom'
        }
        
        // Handle Feerott variations (single 'r' in portal vs double 'r' in filename)
        if (zoneNameLower.includes('feerott') || zoneNameLower.includes('feerrott')) {
          return shortNameLower === 'feerrott'
        }
        
        // Handle Commonlands variations
        if (zoneNameLower.includes('commonlands') || zoneNameLower.includes('the commonlands')) {
          return shortNameLower === 'commons' || shortNameLower === 'commonlands' || 
                 shortNameLower === 'eastcommons' || shortNameLower === 'westcommons'
        }
        
        // Handle Steamfont variations
        if (zoneNameLower.includes('steamfont') && zoneNameLower.includes('mountains')) {
          return shortNameLower === 'steamfont'
        }
        
        // Handle Qeynos variations
        if (zoneNameLower.includes('qeynos') && zoneNameLower.includes('hills')) {
          return shortNameLower === 'qey2hh1' || shortNameLower === 'qeytoqrg'
        }
        
        // Handle Lake variations
        if (zoneNameLower.includes('lake') && zoneNameLower.includes('rathetear')) {
          return shortNameLower === 'lakerathe'
        }
        
        // Handle Rathe Mountains variations
        if (zoneNameLower.includes('rathe') && zoneNameLower.includes('mountains')) {
          return shortNameLower === 'rathemtn'
        }
        
        // Handle Plane of Knowledge variations (most common failure)
        if (zoneNameLower.includes('plane of knowledge') || zoneNameLower.includes('the plane of knowledge')) {
          return shortNameLower === 'poknowledge'
        }
        
        // Handle Plane of Tranquility variations
        if (zoneNameLower.includes('plane of tranquility') || zoneNameLower.includes('the plane of tranquility')) {
          return shortNameLower === 'potranquility'
        }
        
        // Handle Eastern/Western Wastes variations
        if (zoneNameLower.includes('eastern wastes') || zoneNameLower.includes('the eastern wastes')) {
          return shortNameLower === 'eastwastes'
        }
        if (zoneNameLower.includes('western wastes') || zoneNameLower.includes('the western wastes')) {
          return shortNameLower === 'westwastes'
        }
        
        // Handle Field of Scale variations
        if (zoneNameLower.includes('field of scale')) {
          return shortNameLower === 'fieldofscale'
        }
        
        // Handle Iceclad Ocean variations
        if (zoneNameLower.includes('iceclad ocean') || zoneNameLower.includes('the iceclad ocean')) {
          return shortNameLower === 'iceclad'
        }
        
        // Handle The Overthere variations
        if (zoneNameLower.includes('the overthere') || zoneNameLower.includes('overthere')) {
          return shortNameLower === 'overthere'
        }
        
        // Handle Field of Bone variations
        if (zoneNameLower.includes('field of bone') || zoneNameLower.includes('the field of bone')) {
          return shortNameLower === 'fieldofbone'
        }
        
        // Handle Frontier Mountains variations
        if (zoneNameLower.includes('frontier mountains')) {
          return shortNameLower === 'frontier'
        }
        
        // Handle Great Divide variations
        if (zoneNameLower.includes('great divide') || zoneNameLower.includes('the great divide')) {
          return shortNameLower === 'greatdivide'
        }
        
        // Handle Warsliks Woods variations
        if (zoneNameLower.includes('warsliks woods') || zoneNameLower.includes('the warsliks woods')) {
          return shortNameLower === 'warslikswood'
        }
        
        // Handle Swamp of No Hope variations
        if (zoneNameLower.includes('swamp of no hope') || zoneNameLower.includes('the swamp of no hope')) {
          return shortNameLower === 'swampofnohope'
        }
        
        // Handle additional zone variations from second wave analysis
        if (zoneNameLower.includes('lake of ill omen') || zoneNameLower.includes('lake_of_ill_omen')) {
          return shortNameLower === 'lakeofillomen'
        }
        
        if (zoneNameLower.includes('firiona vie')) {
          return shortNameLower === 'firiona'
        }
        
        if (zoneNameLower.includes('cobalt scar')) {
          return shortNameLower === 'cobaltscar'
        }
        
        if (zoneNameLower.includes('the dreadlands') || zoneNameLower.includes('dreadlands')) {
          return shortNameLower === 'dreadlands'
        }
        
        if (zoneNameLower.includes('cabilis east')) {
          return shortNameLower === 'cabeast'
        }
        
        if (zoneNameLower.includes('cabilis west')) {
          return shortNameLower === 'cabwest'
        }
        
        if (zoneNameLower.includes('timorous deep')) {
          return shortNameLower === 'timorous'
        }
        
        if (zoneNameLower.includes('temple of droga') || zoneNameLower.includes('the temple of droga')) {
          return shortNameLower === 'droga'
        }
        
        if (zoneNameLower.includes('echo caverns')) {
          return shortNameLower === 'echocaverns'
        }
        
        if (zoneNameLower.includes('grimling forest')) {
          return shortNameLower === 'grimling'
        }
        
        if (zoneNameLower.includes('dulak') && zoneNameLower.includes('harbor')) {
          return shortNameLower === 'dulak'
        }
        
        if (zoneNameLower.includes('gulf of gunthak') || zoneNameLower.includes('the gulf of gunthak')) {
          return shortNameLower === 'gunthak'
        }
        
        if (zoneNameLower.includes('old bloodfields')) {
          return shortNameLower === 'oldbloodfields' || shortNameLower === 'bloodfields'
        }
        
        if (zoneNameLower.includes('loping plains')) {
          return shortNameLower === 'lopingplains'
        }
        
        if (zoneNameLower.includes('the undershore') || zoneNameLower.includes('undershore')) {
          return shortNameLower === 'undershore'
        }
        
        if (zoneNameLower.includes('buried sea') || zoneNameLower.includes('the buried sea')) {
          return shortNameLower === 'buried' || shortNameLower === 'buriedsea'
        }
        
        if (zoneNameLower.includes('ruins of illsalin')) {
          return shortNameLower === 'ruins' || shortNameLower === 'illsalin'
        }
        
        if (zoneNameLower.includes('nagafen') && zoneNameLower.includes('lair')) {
          return shortNameLower === 'soldungb'
        }
        
        if (zoneNameLower.includes('solusek') && zoneNameLower.includes('eye')) {
          return shortNameLower === 'soldunga'
        }
        
        if (zoneNameLower.includes('lesser faydark') || zoneNameLower.includes('the lesser faydark')) {
          return shortNameLower === 'lfaydark'
        }
        
        // Handle complex modern zone names (systematic approach)
        const zoneAliases = {
          'shard landing': 'shardslanding',
          'shards landing': 'shardslanding',
          'shard`s landing': 'shardslanding',
          'muramite proving grounds': 'provinggrounds',
          'proving grounds': 'provinggrounds',
          'house of thule': 'housethule',
          'scorched woods': 'scorchedwoods',
          'resplendent temple': 'resplendenttemple',
          'sarith city of tides': 'sarith',
          'qinimi court of nihilia': 'qinimi',
          'katta castrum': 'kattacastrum',
          'freeport sewers': 'freeportsewers',
          'drunder fortress of zek': 'drunder',
          'underquarry': 'underquarry',
          'the underquarry': 'underquarry',
          'toskirakk': 'toskirakk',
          'laurion inn': 'laurioninn',
          'korafax home of the riders': 'korafax',
          'fortress mechanotus': 'mechanotus',
          'ethernere tainted west karana': 'ethernerekarana',
          'brell rest': 'brellsrest',
          'brell`s rest': 'brellsrest',
          'the hive': 'hive',
          'east wastes zeixshi-kar awakening': 'eastwastes',
          'zeixshi-kar': 'eastwastes'
        }
        
        for (const [alias, targetShortName] of Object.entries(zoneAliases)) {
          if (zoneNameLower.includes(alias)) {
            return shortNameLower === targetShortName
          }
        }
        
        // Handle Plane variations
        if (zoneNameLower.includes('plane of sky') || zoneNameLower.includes('sky')) {
          return shortNameLower === 'airplane'
        }
        if (zoneNameLower.includes('plane of fear') || zoneNameLower.includes('fear')) {
          return shortNameLower === 'fearplane'
        }
        if (zoneNameLower.includes('plane of hate') || zoneNameLower.includes('hate')) {
          return shortNameLower === 'hateplane' || shortNameLower === 'hateplaneb'
        }
        if (zoneNameLower.includes('plane of growth') || zoneNameLower.includes('growth')) {
          return shortNameLower === 'growthplane'
        }
        if (zoneNameLower.includes('plane of mischief') || zoneNameLower.includes('mischief')) {
          return shortNameLower === 'mischiefplane'
        }
        
        // Handle Castle/Tower variations
        if (zoneNameLower.includes('castle mistmoore') || zoneNameLower.includes('mistmoore')) {
          return shortNameLower === 'mistmoore'
        }
        if (zoneNameLower.includes('tower of frozen shadow') || zoneNameLower.includes('frozen shadow')) {
          return shortNameLower === 'frozenshadow'
        }
        if (zoneNameLower.includes('kurn') && zoneNameLower.includes('tower')) {
          return shortNameLower === 'kurn'
        }
        
        // Handle Erudin variations
        if (zoneNameLower.includes('erudin')) {
          if (zoneNameLower.includes('palace')) return shortNameLower === 'erudnint'
          return shortNameLower === 'erudnext'
        }
        
        // Handle Estate/Lair variations
        if (zoneNameLower.includes('estate') && zoneNameLower.includes('unrest')) {
          return shortNameLower === 'unrest'
        }
        if (zoneNameLower.includes('lair') && zoneNameLower.includes('splitpaw')) {
          return shortNameLower === 'paw'
        }
        
        // Handle Solusek variations
        if (zoneNameLower.includes('solusek') && zoneNameLower.includes('eye')) {
          return shortNameLower === 'soldunga'
        }
        if (zoneNameLower.includes('nagafen') && zoneNameLower.includes('lair')) {
          return shortNameLower === 'soldungb'
        }
        
        // Handle Temple/Keep variations
        if (zoneNameLower.includes('temple') && zoneNameLower.includes('droga')) {
          return shortNameLower === 'droga'
        }
        if (zoneNameLower.includes('mines') && zoneNameLower.includes('nurga')) {
          return shortNameLower === 'nurga'
        }
        if (zoneNameLower.includes('permafrost') && zoneNameLower.includes('keep')) {
          return shortNameLower === 'permafrost'
        }
        
        // Handle Luclin zone variations
        if (zoneNameLower.includes('shadow haven')) {
          return shortNameLower === 'shadowhaven'
        }
        if (zoneNameLower.includes('the nexus') || (zoneNameLower.includes('nexus') && !zoneNameLower.includes('scar'))) {
          return shortNameLower === 'nexus'
        }
        if (zoneNameLower.includes('shar vahl')) {
          return shortNameLower === 'sharvahl'
        }
        if (zoneNameLower.includes('netherbian') && zoneNameLower.includes('lair')) {
          return shortNameLower === 'netherbian'
        }
        if (zoneNameLower.includes('ssraeshza') || zoneNameLower.includes('ssrae')) {
          return shortNameLower === 'ssratemple'
        }
        if (zoneNameLower.includes('grieg') && zoneNameLower.includes('end')) {
          return shortNameLower === 'griegsend'
        }
        if (zoneNameLower.includes('vex thal')) {
          return shortNameLower === 'vexthal'
        }
        
        // Handle Innothule Swamp variations
        if (zoneNameLower.includes('innothule') && zoneNameLower.includes('swamp')) {
          return shortNameLower === 'innothule'
        }
        
        // Handle common "The" prefixes and special cases
        if (zoneNameLower.includes('the ')) {
          const withoutThe = zoneNameLower.replace(/^the\s+/, '')
          if (longNameLower.includes(withoutThe) || shortNameLower.includes(withoutThe)) {
            return true
          }
        }
        
        // Handle "of" variations (Lake of Ill Omen, etc.)
        if (zoneNameLower.includes(' of ')) {
          const parts = zoneNameLower.split(' of ')
          if (parts.length === 2) {
            const firstPart = parts[0].trim()
            const secondPart = parts[1].trim()
            if ((longNameLower.includes(firstPart) && longNameLower.includes(secondPart)) ||
                shortNameLower.includes(firstPart.replace(/\s+/g, '')) ||
                shortNameLower.includes(secondPart.replace(/\s+/g, ''))) {
              return true
            }
          }
        }
        
        // Handle Kunark zone variations
        if (zoneNameLower.includes('emerald') && zoneNameLower.includes('jungle')) {
          return shortNameLower === 'emeraldjungle'
        }
        if (zoneNameLower.includes('firiona') && zoneNameLower.includes('vie')) {
          return shortNameLower === 'firiona'
        }
        if (zoneNameLower.includes('field') && zoneNameLower.includes('bone')) {
          return shortNameLower === 'fieldofbone'
        }
        if (zoneNameLower.includes('burning') && zoneNameLower.includes('wood')) {
          return shortNameLower === 'burningwood' || shortNameLower === 'burning'
        }
        if (zoneNameLower.includes('skyfire') && zoneNameLower.includes('mountain')) {
          return shortNameLower === 'skyfire'
        }
        if (zoneNameLower.includes('frontier') && zoneNameLower.includes('mountain')) {
          return shortNameLower === 'frontier'
        }
        if (zoneNameLower.includes('trakanon') && zoneNameLower.includes('teeth')) {
          return shortNameLower === 'trakanon'
        }
        if (zoneNameLower.includes('timorous') && zoneNameLower.includes('deep')) {
          return shortNameLower === 'timorous'
        }
        if (zoneNameLower.includes('halls') && zoneNameLower.includes('betrayal')) {
          return shortNameLower === 'chardokb'
        }
        if (zoneNameLower.includes('old') && zoneNameLower.includes('sebilis')) {
          return shortNameLower === 'sebilis' || shortNameLower === 'oldsebilis'
        }
        if (zoneNameLower.includes('city') && zoneNameLower.includes('mist')) {
          return shortNameLower === 'citymist'
        }
        if (zoneNameLower.includes('howling') && zoneNameLower.includes('stone')) {
          return shortNameLower === 'howlingstones' || shortNameLower === 'charasis'
        }
        
        // Handle Velious zone variations
        if (zoneNameLower.includes('eastern') && zoneNameLower.includes('waste')) {
          return shortNameLower === 'eastwastes'
        }
        if (zoneNameLower.includes('western') && zoneNameLower.includes('waste')) {
          return shortNameLower === 'westwastes'
        }
        if (zoneNameLower.includes('iceclad') && zoneNameLower.includes('ocean')) {
          return shortNameLower === 'iceclad'
        }
        if (zoneNameLower.includes('cobalt') && zoneNameLower.includes('scar')) {
          return shortNameLower === 'cobaltscar'
        }
        if (zoneNameLower.includes('great') && zoneNameLower.includes('divide')) {
          return shortNameLower === 'greatdivide'
        }
        if (zoneNameLower.includes('wakening') && zoneNameLower.includes('land')) {
          return shortNameLower === 'wakening' || shortNameLower === 'wakeningland'
        }
        if (zoneNameLower.includes('crystal') && zoneNameLower.includes('cavern')) {
          return shortNameLower === 'crystal' || shortNameLower === 'crystalcaverns'
        }
        if (zoneNameLower.includes('dragon') && zoneNameLower.includes('necropolis')) {
          return shortNameLower === 'necropolis' || shortNameLower === 'dragnecro'
        }
        if (zoneNameLower.includes('temple') && zoneNameLower.includes('veeshan')) {
          return shortNameLower === 'templeveeshan'
        }
        if (zoneNameLower.includes('kael') && zoneNameLower.includes('drakkel')) {
          return shortNameLower === 'kael' || shortNameLower === 'kaeldrakkel'
        }
        if (zoneNameLower.includes('sleeper') && zoneNameLower.includes('tomb')) {
          return shortNameLower === 'sleeper' || shortNameLower === 'sleepers' || shortNameLower === 'sleeperstomb'
        }
        if (zoneNameLower.includes('siren') && zoneNameLower.includes('grotto')) {
          return shortNameLower === 'sirens' || shortNameLower === 'sirensgrotto'
        }
        
        // Handle common abbreviations and contractions
        if (zoneNameLower.includes("'")) {
          const withoutApostrophe = zoneNameLower.replace(/'/g, '')
          if (longNameLower.includes(withoutApostrophe) || shortNameLower.includes(withoutApostrophe)) {
            return true
          }
        }
        
        // Handle zone variations like "to_" prefixes
        const cleanZoneName = zoneNameLower.replace(/^to_/, '').replace(/_/g, '').replace(/\s+/g, '')
        const cleanShortName = shortNameLower.replace(/_/g, '')
        const cleanLongName = longNameLower.replace(/\s+/g, '').replace(/'/g, '')
        
        if (cleanShortName === cleanZoneName || cleanLongName.includes(cleanZoneName)) {
          return true
        }
        
        // Handle partial word matching for complex zone names
        const zoneWords = zoneNameLower.split(/\s+/)
        const longWords = longNameLower.split(/\s+/)
        
        if (zoneWords.length >= 2 && longWords.length >= 2) {
          const matchCount = zoneWords.filter(word => 
            word.length > 3 && longWords.some(lw => lw.includes(word) || word.includes(lw))
          ).length
          
          if (matchCount >= Math.min(2, zoneWords.length)) {
            return true
          }
        }
        
        return false
      })
      
      if (matchedZone) {
        try {
          selectZone(matchedZone)
        } catch (error) {
          console.error('Error during zone navigation:', error)
        }
      } else {
        console.warn(`Could not find zone matching "${zoneName}"`)
      }
    }
    
    const clearSearch = () => {
      searchQuery.value = ''
      searchResults.value = []
      highlightedIndex.value = -1
    }
    
    const handleKeydown = (event) => {
      switch (event.key) {
        case 'ArrowDown':
          if (!searchResults.value.length) return
          event.preventDefault()
          highlightedIndex.value = Math.min(highlightedIndex.value + 1, searchResults.value.length - 1)
          break
          
        case 'ArrowUp':
          if (!searchResults.value.length) return
          event.preventDefault()
          highlightedIndex.value = Math.max(highlightedIndex.value - 1, 0)
          break
          
        case 'Enter':
          event.preventDefault()
          if (highlightedIndex.value >= 0 && highlightedIndex.value < searchResults.value.length) {
            const selectedZoneData = searchResults.value[highlightedIndex.value]
            searchResults.value = [] // Clear dropdown immediately
            highlightedIndex.value = -1 // Reset highlight
            selectZone(selectedZoneData)
          } else {
            // If no item is highlighted or no results, just clear the dropdown
            searchResults.value = []
            highlightedIndex.value = -1
          }
          break
          
        case 'Escape':
          event.preventDefault()
          clearSearch()
          break
      }
    }
    
    // Watch for search query changes
    watch(searchQuery, () => {
      if (!isSettingSearchQuery.value) {
        handleSearch()
      }
    })
    
    // Watch for zone changes to reset collapsed state
    watch(selectedZone, () => {
      if (selectedZone.value) {
        collapsedGroups.value = []
        allGroupsCollapsed.value = true
      }
    })
    
    // Watch for new item data to initialize collapsed state
    watch(groupedZoneItems, (newGroups) => {
      if (newGroups.length > 0 && collapsedGroups.value.length === 0) {
        console.log('Initializing collapsed state for', newGroups.length, 'groups')
        collapsedGroups.value = newGroups.map(group => group.type)
        allGroupsCollapsed.value = true
        console.log('Initialized collapsed groups:', collapsedGroups.value)
      }
    }, { immediate: true })
    
    const getItemTypeDisplay = (itemtype) => {
      const typeMap = {
        0: '1H Slashing',
        1: '2H Slashing',
        2: '1H Piercing',
        3: '1H Blunt',
        4: '2H Blunt',
        5: 'Archery',
        7: 'Throwing',
        8: 'Shield',
        10: 'Armor',
        11: 'Tradeskill Item',
        12: 'Lockpicking',
        14: 'Food',
        15: 'Drink',
        16: 'Light Source',
        17: 'Common Inventory Item',
        18: 'Bind Wound',
        19: 'Thrown Casting Item',
        20: 'Spells / Song Sheets',
        21: 'Potions',
        22: 'Fletched Arrows',
        23: 'Wind Instrument',
        24: 'Stringed Instrument',
        25: 'Brass Instrument',
        26: 'Percussion Instrument',
        27: 'Ammo',
        29: 'Jewelry',
        31: 'Readable Note/Scroll',
        32: 'Readable Book',
        33: 'Key',
        34: 'Odd Item',
        35: '2H Piercing',
        36: 'Fishing Pole',
        37: 'Fishing Bait',
        38: 'Alcoholic Beverage',
        39: 'More Keys',
        40: 'Compass',
        42: 'Poison',
        45: 'Hand to Hand',
        52: 'Charm',
        53: 'Dye',
        54: 'Augment',
        55: 'Augment Solvent',
        56: 'Augment Distiller',
        58: 'Fellowship Banner Material',
        60: 'Cultural Armor Manual',
        63: 'New Currency',
      }
      return typeMap[itemtype] || `Type ${itemtype}`
    }
    
    // Handle zone query parameter on mount
    onMounted(async () => {
      const zoneParam = route.query.zone
      if (zoneParam) {
        console.log('Zone parameter detected:', zoneParam)
        
        // Small delay to ensure component is fully initialized
        await new Promise(resolve => setTimeout(resolve, 100))
        
        // Set search query to trigger filtering
        isSettingSearchQuery.value = true
        searchQuery.value = zoneParam
        isSettingSearchQuery.value = false
        
        // Trigger search to populate results
        handleSearch()
        
        console.log('Filtered zones after search:', filteredZones.value.map(z => z.longName))
        
        // Enhanced zone matching to handle variations like "The Greater Faydark" vs "Greater Faydark"
        // Search in availableZones (full list) rather than filteredZones (partial matches only)
        const exactMatch = availableZones.value.find(zone => {
          const zoneLong = zone.longName.toLowerCase()
          const zoneShort = zone.shortName.toLowerCase()
          const param = zoneParam.toLowerCase()
          
          // Exact matches
          if (zoneLong === param || zoneShort === param) {
            return true
          }
          
          // Handle "The" prefix variations
          const paramWithoutThe = param.replace(/^the\s+/, '')
          const zoneWithoutThe = zoneLong.replace(/^the\s+/, '')
          
          if (zoneWithoutThe === paramWithoutThe || zoneLong === paramWithoutThe || zoneShort === paramWithoutThe) {
            return true
          }
          
          return false
        })
        
        console.log('Exact match found:', exactMatch)
        
        if (exactMatch) {
          console.log('Auto-selecting zone:', exactMatch.longName)
          await selectZone(exactMatch)
        } else {
          console.warn(`Could not find zone matching "${zoneParam}" in available zones`)
        }
      }
    })
    
    return {
      loading,
      mapLoading,
      searchQuery,
      searchResults,
      highlightedIndex,
      selectedZone,
      mapLines,
      mapLabels,
      activeTab,
      tabs,
      zoneNpcs,
      uniqueZoneNpcs,
      selectedNpcForMap,
      npcsLoading,
      zoneItems,
      uniqueZoneItems,
      groupedZoneItems,
      itemsLoading,
      handleSearch,
      selectZone,
      clearSelection,
      handleNpcClick,
      plotNpcOnMap,
      openNpcInfo,
      handleItemIconError,
      openItemInfo,
      handleZoneNavigation,
      clearSearch,
      handleKeydown,
      formatRespawnTime,
      getItemTypeDisplay,
      collapsedGroups,
      allGroupsCollapsed,
      toggleGroup,
      toggleAllGroups,
      isGroupCollapsed,
      getExpansionForZone,
      getExpansionName,
      getExpansionIcon
    }
  }
}
</script>

<style scoped>
.zones-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  color: #e5e7eb;
  background: linear-gradient(135deg, #111827, #1f2937);
  min-height: 100vh;
}

.zones-header {
  text-align: center;
  margin-bottom: 2rem;
}

.zones-header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  color: #a78bfa;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.zones-header p {
  font-size: 1.1rem;
  opacity: 0.8;
}

.zones-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.zone-search-section {
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
}

.search-container {
  position: relative;
}

.zone-search-input {
  width: 100%;
  padding: 1rem 1.5rem;
  font-size: 1.1rem;
  border: 2px solid rgba(75, 85, 99, 0.5);
  border-radius: 12px;
  background: rgba(31, 41, 55, 0.8);
  backdrop-filter: blur(10px);
  color: #e5e7eb;
  transition: all 0.3s ease;
}

.zone-search-input:focus {
  outline: none;
  border-color: #a78bfa;
  box-shadow: 0 0 20px rgba(167, 139, 250, 0.4);
}

.zone-search-input::placeholder {
  color: rgba(156, 163, 175, 0.8);
}

.search-clear-btn {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  color: rgba(156, 163, 175, 0.6);
  font-size: 1.5rem;
  font-weight: bold;
  cursor: pointer;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
  z-index: 10;
}

.search-clear-btn:hover {
  color: #e5e7eb;
  background: rgba(75, 85, 99, 0.3);
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: rgba(17, 24, 39, 0.98);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(75, 85, 99, 0.6);
  border-radius: 8px;
  margin-top: 0.5rem;
  max-height: 400px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.search-result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  cursor: pointer;
  border-bottom: 1px solid rgba(75, 85, 99, 0.3);
  transition: all 0.2s ease;
}

.search-result-item:hover,
.search-result-item.highlighted {
  background: rgba(167, 139, 250, 0.1);
}

.search-result-item:last-child {
  border-bottom: none;
}

.zone-info .zone-name {
  font-weight: bold;
  font-size: 1rem;
}

.zone-info .zone-short-name {
  font-size: 0.9rem;
  opacity: 0.7;
  margin-top: 0.2rem;
}

.expansion-icon {
  flex-shrink: 0;
  margin-left: 1rem;
}

.expansion-icon img {
  width: 72px;
  height: 43px;
  border-radius: 4px;
  opacity: 0.8;
  transition: opacity 0.2s ease;
  image-rendering: pixelated;
  object-fit: contain;
}

.search-result-item:hover .expansion-icon img {
  opacity: 1;
}

.selected-zone-section {
  width: 100%;
}

.zone-details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.zone-details-header h2 {
  font-size: 2rem;
  color: #a78bfa;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.zone-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.zone-short {
  background: rgba(75, 85, 99, 0.4);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
  color: #a78bfa;
  border: 1px solid rgba(167, 139, 250, 0.3);
}

.clear-btn {
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.5);
  color: #f87171;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.clear-btn:hover {
  background: rgba(239, 68, 68, 0.3);
  color: #fca5a5;
}

.zone-map-container {
  width: 100%;
  height: 600px;
  margin-bottom: 2rem;
  border: 2px solid rgba(75, 85, 99, 0.5);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(17, 24, 39, 0.8);
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3);
}

.zone-info-tabs {
  width: 100%;
}

.tab-buttons {
  display: flex;
  border-bottom: 2px solid rgba(75, 85, 99, 0.5);
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.tab-btn {
  background: transparent;
  border: none;
  color: rgba(156, 163, 175, 0.8);
  padding: 1rem 2rem;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s ease;
  border-bottom: 3px solid transparent;
}

.tab-btn:hover {
  color: #e5e7eb;
  background: rgba(75, 85, 99, 0.2);
}

.tab-btn.active {
  color: #a78bfa;
  border-bottom-color: #a78bfa;
}

.tab-content {
  min-height: 200px;
}

.tab-panel {
  animation: fadeIn 0.3s ease;
}

.tab-panel h3 {
  color: #a78bfa;
  margin-bottom: 1rem;
}

.no-zone-selected {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.zone-placeholder {
  text-align: center;
  opacity: 0.8;
}

.treasure-map {
  margin-bottom: 2rem;
  perspective: 1000px;
  filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.4));
}

.treasure-map svg {
  animation: mapFloat 8s ease-in-out infinite;
  max-width: 100%;
  height: auto;
  transform-style: preserve-3d;
  transform: perspective(800px) rotateX(5deg) rotateY(-2deg);
  cursor: pointer;
}

@keyframes mapFloat {
  0%, 100% {
    transform: perspective(800px) rotateX(5deg) rotateY(-2deg) translateY(0px) rotate(0deg);
  }
  25% {
    transform: perspective(800px) rotateX(6deg) rotateY(-1deg) translateY(-3px) rotate(0.3deg);
  }
  50% {
    transform: perspective(800px) rotateX(4deg) rotateY(-3deg) translateY(-8px) rotate(0.8deg);
  }
  75% {
    transform: perspective(800px) rotateX(7deg) rotateY(-2deg) translateY(-3px) rotate(-0.3deg);
  }
}

.treasure-map:hover svg {
  animation-duration: 4s;
  transform: perspective(800px) rotateX(2deg) rotateY(-1deg) scale(1.02);
  transition: transform 0.3s ease;
}

/* Add subtle pulsing animation to the X mark */
.treasure-map svg g:last-of-type path {
  animation: treasurePulse 2s ease-in-out infinite;
}

@keyframes treasurePulse {
  0%, 100% {
    opacity: 0.8;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.1);
  }
}

.zone-placeholder h3 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: #a78bfa;
}

.zone-placeholder p {
  opacity: 0.7;
  font-size: 1.1rem;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .zones-container {
    padding: 1rem;
  }
  
  .zones-header h1 {
    font-size: 2rem;
  }
  
  .zone-details-header {
    flex-direction: column;
    align-items: stretch;
    text-align: center;
  }
  
  .zone-meta {
    justify-content: center;
  }
  
  .zone-map-container {
    height: 400px;
  }
  
  .tab-buttons {
    justify-content: center;
  }
  
  .tab-btn {
    padding: 0.8rem 1.5rem;
  }
}

/* NPC List Styles */
.npcs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.npcs-header h3 {
  margin: 0;
  color: #a78bfa;
}

.npcs-summary {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.clear-npc-selection-btn {
  background: linear-gradient(135deg, #dc2626, #b91c1c);
  color: white;
  border: 1px solid rgba(220, 38, 38, 0.4);
  border-radius: 6px;
  padding: 0.25rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.clear-npc-selection-btn:hover {
  background: linear-gradient(135deg, #b91c1c, #991b1b);
  border-color: rgba(220, 38, 38, 0.6);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.3);
}

.npc-count {
  color: #10b981;
  font-weight: 600;
}

.no-npcs {
  color: #6b7280;
}

.loading-text {
  color: #a78bfa;
  font-style: italic;
}


.no-npcs-message {
  text-align: center;
  padding: 4rem 2rem;
  color: #6b7280;
}

.no-data-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.no-npcs-message h4 {
  color: #9ca3af;
  margin-bottom: 1rem;
}

.npcs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 0.75rem;
}

/* Compact NPC Card Styles */
.npc-card-compact {
  background: rgba(31, 41, 55, 0.8);
  border: 1px solid rgba(75, 85, 99, 0.4);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  transition: all 0.2s ease;
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-height: 60px;
}

.npc-card-compact:hover {
  border-color: rgba(167, 139, 250, 0.6);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3), 0 0 12px rgba(167, 139, 250, 0.15);
  background: rgba(31, 41, 55, 0.9);
}

.npc-card-compact.npc-selected {
  border-color: rgba(16, 185, 129, 0.8);
  background: rgba(31, 41, 55, 0.95);
  box-shadow: 0 2px 12px rgba(16, 185, 129, 0.3), 0 0 20px rgba(16, 185, 129, 0.2);
}

.npc-card-compact.npc-selected .npc-name-compact {
  color: rgba(16, 185, 129, 0.95);
}

.npc-card-compact.npc-selected .map-pin-btn {
  background: linear-gradient(135deg, #047857, #065f46);
  border-color: rgba(16, 185, 129, 0.6);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4);
}

.npc-basic-info {
  flex: 1;
  min-width: 0; /* Allow text truncation */
}

.npc-name-compact {
  font-size: 0.95rem;
  font-weight: 600;
  color: #f3f4f6;
  line-height: 1.2;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  gap: 6px;
}

.npc-card-compact.clickable-npc-card {
  cursor: pointer;
  transition: all 0.2s ease;
}

.npc-card-compact.clickable-npc-card:hover {
  background: rgba(96, 165, 250, 0.1);
  border-color: rgba(96, 165, 250, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(96, 165, 250, 0.2);
}

.npc-card-compact.clickable-npc-card:hover .npc-name-compact {
  color: #60a5fa;
}

.npc-link-icon {
  font-size: 8px;
  color: #9ca3af;
  opacity: 0.7;
  transition: all 0.2s ease;
  margin-left: auto;
  flex-shrink: 0;
}

.npc-card-compact.clickable-npc-card:hover .npc-link-icon {
  opacity: 1;
  color: #60a5fa;
}

.spawn-count-badge {
  font-size: 0.75rem;
  font-weight: 500;
  color: #fbbf24;
  background: rgba(245, 158, 11, 0.15);
  padding: 0.125rem 0.375rem;
  border-radius: 0.375rem;
  margin-left: 0.5rem;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.npc-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.npc-level-compact {
  background: linear-gradient(135deg, #a78bfa, #8b5cf6);
  color: white;
  padding: 0.15rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  box-shadow: 0 1px 4px rgba(167, 139, 250, 0.3);
}

.npc-respawn-compact {
  color: #10b981;
  font-size: 0.8rem;
  font-weight: 500;
  white-space: nowrap;
}

.npc-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.npc-action-btn {
  background: rgba(75, 85, 99, 0.6);
  border: 1px solid rgba(107, 114, 128, 0.4);
  border-radius: 6px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.9rem;
  padding: 0;
}

.npc-action-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.map-pin-btn {
  background: linear-gradient(135deg, #10b981, #059669);
  border-color: rgba(16, 185, 129, 0.4);
  color: white;
}

.map-pin-btn:hover {
  background: linear-gradient(135deg, #059669, #047857);
  border-color: rgba(16, 185, 129, 0.6);
  box-shadow: 0 2px 12px rgba(16, 185, 129, 0.4);
}

.info-btn {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border-color: rgba(59, 130, 246, 0.4);
  color: white;
}

.info-btn:hover {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  border-color: rgba(59, 130, 246, 0.6);
  box-shadow: 0 2px 12px rgba(59, 130, 246, 0.4);
}

/* Responsive Design */
@media (max-width: 768px) {
  .npcs-grid {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
  
  .npc-card-compact {
    padding: 0.5rem 0.75rem;
    min-height: 56px;
  }
  
  .npc-name-compact {
    font-size: 0.9rem;
  }
  
  .npc-level-compact {
    font-size: 0.7rem;
    padding: 0.1rem 0.4rem;
  }
  
  .npc-respawn-compact {
    font-size: 0.75rem;
  }
  
  .npc-action-btn {
    width: 28px;
    height: 28px;
    font-size: 0.8rem;
  }
  
  .npcs-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
}

@media (max-width: 480px) {
  .npc-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .npc-card-compact {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
    min-height: auto;
    padding: 0.75rem;
  }
  
  .npc-actions {
    justify-content: center;
    gap: 1rem;
  }
  
  .npc-action-btn {
    width: 36px;
    height: 36px;
    font-size: 1rem;
  }
}

/* ===== ITEM STYLES ===== */
.items-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  gap: 1rem;
}

.items-header h3 {
  margin: 0;
  font-size: 1.5rem;
  color: #f3f4f6;
}

.items-summary {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.item-count {
  color: #10b981;
  font-weight: 600;
}


.no-items-message {
  text-align: center;
  padding: 4rem 2rem;
  color: #9ca3af;
}

.no-items-message .no-data-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.7;
}

.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
}

.item-card-compact {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(31, 41, 55, 0.6);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(75, 85, 99, 0.4);
  border-radius: 0.75rem;
  transition: all 0.3s ease;
  min-height: 68px;
}

.item-card-compact:hover {
  border-color: rgba(59, 130, 246, 0.6);
  background: rgba(31, 41, 55, 0.8);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.item-icon-container {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 0.5rem;
  border: 1px solid rgba(75, 85, 99, 0.3);
}

.item-icon {
  width: 32px;
  height: 32px;
  object-fit: contain;
  image-rendering: pixelated;
}

.item-basic-info {
  flex: 1;
  min-width: 0;
}

.item-name-compact {
  font-size: 0.95rem;
  font-weight: 600;
  color: #f3f4f6;
  line-height: 1.2;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.item-stat {
  color: #9ca3af;
  font-size: 0.8rem;
  font-weight: 500;
  white-space: nowrap;
}

.drop-count-badge {
  font-size: 0.75rem;
  font-weight: 500;
  color: #06b6d4;
  background: rgba(6, 182, 212, 0.15);
  padding: 0.125rem 0.375rem;
  border-radius: 0.375rem;
  margin-left: 0.5rem;
  border: 1px solid rgba(6, 182, 212, 0.3);
}

.item-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.item-action-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-action-btn.info-btn {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
}

.item-action-btn.info-btn:hover {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(37, 99, 235, 0.3);
}

/* Responsive Design */
@media (max-width: 768px) {
  .items-grid {
    grid-template-columns: 1fr;
  }
  
  .item-card-compact {
    padding: 0.5rem 0.75rem;
    min-height: 56px;
  }
  
  .item-name-compact {
    font-size: 0.9rem;
  }
  
  .item-stat {
    font-size: 0.75rem;
  }
  
  .item-action-btn {
    width: 28px;
    height: 28px;
    font-size: 0.8rem;
  }
}

@media (max-width: 480px) {
  .item-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .item-card-compact {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
    min-height: auto;
    padding: 0.75rem;
  }
  
  .item-actions {
    justify-content: center;
    gap: 1rem;
  }
  
  .item-action-btn {
    width: 36px;
    height: 36px;
    font-size: 1rem;
  }
}

.item-type {
  background: rgba(102, 126, 234, 0.2);
  color: #a78bfa;
  padding: 0.2rem 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
  display: inline-block;
}

.item-type-group {
  margin-bottom: 2rem;
}

.item-type-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid rgba(102, 126, 234, 0.3);
}

.item-type-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #a78bfa;
}

.item-type-count {
  background: rgba(102, 126, 234, 0.2);
  color: #a78bfa;
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.8rem;
  font-weight: 500;
}

.clickable-item {
  cursor: pointer;
  transition: all 0.2s ease;
}

.clickable-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  border-color: rgba(102, 126, 234, 0.6);
}

.items-controls {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1.5rem;
}

.toggle-all-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(102, 126, 234, 0.2);
  color: #a78bfa;
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 0.375rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-all-btn:hover {
  background: rgba(102, 126, 234, 0.3);
  border-color: rgba(102, 126, 234, 0.5);
  transform: translateY(-1px);
}

.clickable-header {
  cursor: pointer;
  transition: all 0.2s ease;
}

.clickable-header:hover {
  background: rgba(102, 126, 234, 0.1);
  border-radius: 0.375rem;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.expand-icon {
  color: #a78bfa;
  font-size: 0.8rem;
  transition: transform 0.2s ease;
}
</style>