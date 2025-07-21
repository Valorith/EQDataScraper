<template>
  <div class="npcs-page">
    <div class="page-header">
      <h1>NPC Database</h1>
      <p class="subtitle">Search and explore NPCs from the database</p>
    </div>

    <!-- Search Section -->
    <div class="search-section">
      <div class="search-container">
        <div class="search-input-group">
          <input
            v-model="searchQuery"
            @keyup.enter="performSearch()"
            type="text"
            placeholder="Search NPCs by name..."
            class="search-input"
          />
          <button @click="performSearch()" class="search-button" :disabled="searching">
            <i :class="searching ? 'fas fa-spinner fa-spin' : 'fas fa-search'"></i>
            <span class="search-button-text">{{ searching ? 'Searching...' : 'Search' }}</span>
          </button>
        </div>
        
        <!-- Filters -->
        <div class="filters-container">
          <div class="filter-group">
            <label for="level-min">Min Level:</label>
            <input 
              id="level-min"
              v-model="minLevel" 
              type="number" 
              class="filter-input"
              placeholder="1"
              min="1"
              max="255"
            />
          </div>
          
          <div class="filter-group">
            <label for="level-max">Max Level:</label>
            <input 
              id="level-max"
              v-model="maxLevel" 
              type="number" 
              class="filter-input"
              placeholder="255"
              min="1"
              max="255"
            />
          </div>
          
          <div class="filter-group">
            <label for="zone-filter">Zone:</label>
            <select id="zone-filter" v-model="selectedZone" class="filter-select">
              <option value="">All Zones</option>
              <!-- Zone options will be populated dynamically -->
            </select>
          </div>
          
          <button @click="clearFilters" class="clear-filters-button">
            <i class="fas fa-times"></i>
            Clear Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Loading Modal for Search -->
    <LoadingModal 
      :visible="searching" 
      text="Searching NPCs..." 
    />

    <!-- Loading Modal for Pagination -->
    <LoadingModal 
      :visible="paginating" 
      text="Loading more results..." 
    />

    <!-- Results Section -->
    <div v-if="searchPerformed" class="results-section">
      <div class="results-header">
        <div class="results-info-container">
          <h2>Search Results</h2>
          <div class="results-info">
            <span>{{ totalCount.toLocaleString() }} NPC{{ totalCount !== 1 ? 's' : '' }} found</span>
            <span v-if="searchQuery">(searching for "{{ searchQuery }}")</span>
          </div>
        </div>
        
        <!-- View Toggle -->
        <div class="view-toggle-container">
          <span class="view-toggle-label">View:</span>
          <div class="view-toggle">
            <button 
              @click="viewMode = 'list'" 
              :class="['view-button', { active: viewMode === 'list' }]"
              title="List View"
            >
              <i class="fas fa-list"></i>
              <span class="view-button-text">List</span>
            </button>
            <button 
              @click="viewMode = 'grid'" 
              :class="['view-button', { active: viewMode === 'grid' }]"
              title="Grid View"
            >
              <i class="fas fa-th"></i>
              <span class="view-button-text">Grid</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Results Display -->
      <div v-if="searchResults.length > 0" :class="['npc-results', viewMode]">
        <!-- List View -->
        <div v-if="viewMode === 'list'" class="npc-list">
          <div 
            v-for="npc in searchResults" 
            :key="npc.id"
            @click="openNPCModal(npc)"
            class="npc-row"
          >
            <div class="npc-main-info">
              <div class="npc-name-section">
                <h3 class="npc-name">{{ npc.name }}</h3>
                <div class="npc-details">
                  <span class="npc-level">Level {{ npc.level }}</span>
                  <span class="npc-separator">•</span>
                  <span class="npc-race">{{ getRaceName(npc.race) }}</span>
                  <span class="npc-separator">•</span>
                  <span class="npc-class">{{ getClassName(npc.class) }}</span>
                </div>
              </div>
            </div>
            <div v-if="npc.zone_short_name" class="npc-zone-display">
              <span class="zone-name">{{ getFormattedZoneName(npc) }}</span>
            </div>
          </div>
        </div>

        <!-- Grid View -->
        <div v-if="viewMode === 'grid'" class="npc-grid">
          <div 
            v-for="npc in searchResults" 
            :key="npc.id"
            @click="openNPCModal(npc)"
            class="npc-card"
          >
            <div class="npc-card-header">
              <h3 class="npc-name">{{ npc.name }}</h3>
              <span class="npc-level">Level {{ npc.level }}</span>
            </div>
            <div class="npc-card-body">
              <div class="npc-info">
                <span class="npc-race">{{ getRaceName(npc.race) }}</span>
                <span class="npc-class">{{ getClassName(npc.class) }}</span>
              </div>
              <div class="npc-stats">
                <span class="npc-hp">{{ npc.hp?.toLocaleString() }} HP</span>
                <span v-if="npc.mindmg || npc.maxdmg" class="npc-damage">
                  {{ npc.mindmg }}-{{ npc.maxdmg }} dmg
                </span>
              </div>
              <div v-if="npc.zone_short_name" class="npc-zone">
                Zone: {{ npc.zone_long_name || npc.zone_short_name }}
              </div>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="pagination">
          <button 
            @click="goToPage(1)"
            :disabled="currentPage === 1"
            class="pagination-button"
            title="First page"
          >
            <i class="fas fa-angle-double-left"></i>
          </button>
          
          <button 
            @click="goToPage(currentPage - 1)"
            :disabled="currentPage === 1"
            class="pagination-button"
            title="Previous page"
          >
            <i class="fas fa-angle-left"></i>
          </button>
          
          <span class="pagination-info">
            Page {{ currentPage }} of {{ totalPages }}
          </span>
          
          <button 
            @click="goToPage(currentPage + 1)"
            :disabled="currentPage === totalPages"
            class="pagination-button"
            title="Next page"
          >
            <i class="fas fa-angle-right"></i>
          </button>
          
          <button 
            @click="goToPage(totalPages)"
            :disabled="currentPage === totalPages"
            class="pagination-button"
            title="Last page"
          >
            <i class="fas fa-angle-double-right"></i>
          </button>
        </div>
      </div>

      <!-- No Results -->
      <div v-else class="no-results">
        <div class="no-results-content">
          <i class="fas fa-search"></i>
          <h3>No NPCs Found</h3>
          <p>Try adjusting your search criteria or filters.</p>
        </div>
      </div>
    </div>

    <!-- NPC Details Loading Modal -->
    <LoadingModal 
      :visible="loadingNPCDetails" 
      text="Loading NPC details..." 
      :full-screen="true" 
    />

    <!-- NPC Details Modal -->
    <div v-if="selectedNPCDetail && !loadingNPCDetails" class="modal-overlay" @click="closeNPCModal">
      <div class="modal-content npc-modal" @click.stop>
        <div class="modal-header">
          <div class="modal-header-content">
            <div class="npc-header-info">
              <h3>{{ selectedNPCDetail.name }}</h3>
              <div class="npc-header-meta">
                <span class="npc-id-badge">ID: {{ selectedNPCDetail.id }}</span>
                <span class="level-badge">Level {{ selectedNPCDetail.level }}</span>
                <span class="race-badge">{{ getRaceName(selectedNPCDetail.race) }}</span>
                <span class="class-badge">{{ getClassName(selectedNPCDetail.class) }}</span>
              </div>
            </div>
          </div>
          <button @click="closeNPCModal" class="modal-close">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="modal-body">
          <!-- Basic Information -->
          <div class="detail-section">
            <h4>Basic Information</h4>
            <div class="info-grid">
              <div class="info-row">
                <span class="info-label">Full Name:</span>
                <span class="info-value">{{ selectedNPCDetail.name }}</span>
              </div>
              <div v-if="selectedNPCDetail.lastname" class="info-row">
                <span class="info-label">Last Name:</span>
                <span class="info-value">{{ selectedNPCDetail.lastname }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Level:</span>
                <span class="info-value">{{ selectedNPCDetail.level }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Race:</span>
                <span class="info-value">{{ getRaceName(selectedNPCDetail.race) }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Class:</span>
                <span class="info-value">{{ getClassName(selectedNPCDetail.class) }}</span>
              </div>
            </div>
          </div>

          <!-- Combat Stats -->
          <div class="detail-section">
            <h4>Combat Stats</h4>
            <div class="info-grid">
              <div class="info-row">
                <span class="info-label">Health Points:</span>
                <span class="info-value">{{ selectedNPCDetail.hp?.toLocaleString() }}</span>
              </div>
              <div v-if="selectedNPCDetail.mana" class="info-row">
                <span class="info-label">Mana:</span>
                <span class="info-value">{{ selectedNPCDetail.mana?.toLocaleString() }}</span>
              </div>
              <div v-if="selectedNPCDetail.ac" class="info-row">
                <span class="info-label">Armor Class:</span>
                <span class="info-value">{{ selectedNPCDetail.ac }}</span>
              </div>
              <div v-if="selectedNPCDetail.mindmg || selectedNPCDetail.maxdmg" class="info-row">
                <span class="info-label">Damage:</span>
                <span class="info-value">{{ selectedNPCDetail.mindmg }} to {{ selectedNPCDetail.maxdmg }}</span>
              </div>
              <div v-if="selectedNPCDetail.attack_speed" class="info-row">
                <span class="info-label">Attack Speed:</span>
                <span class="info-value">{{ selectedNPCDetail.attack_speed }}%</span>
              </div>
              <div v-if="selectedNPCDetail.attack_delay" class="info-row">
                <span class="info-label">Attack Delay:</span>
                <span class="info-value">{{ selectedNPCDetail.attack_delay }}</span>
              </div>
            </div>
          </div>

          <!-- Resistances -->
          <div v-if="selectedNPCDetail.resistances && hasResistances" class="detail-section">
            <h4>Resistances</h4>
            <div class="info-grid">
              <div v-if="selectedNPCDetail.resistances.magic" class="info-row">
                <span class="info-label">Magic Resistance:</span>
                <span class="info-value">{{ selectedNPCDetail.resistances.magic }}</span>
              </div>
              <div v-if="selectedNPCDetail.resistances.cold" class="info-row">
                <span class="info-label">Cold Resistance:</span>
                <span class="info-value">{{ selectedNPCDetail.resistances.cold }}</span>
              </div>
              <div v-if="selectedNPCDetail.resistances.disease" class="info-row">
                <span class="info-label">Disease Resistance:</span>
                <span class="info-value">{{ selectedNPCDetail.resistances.disease }}</span>
              </div>
              <div v-if="selectedNPCDetail.resistances.fire" class="info-row">
                <span class="info-label">Fire Resistance:</span>
                <span class="info-value">{{ selectedNPCDetail.resistances.fire }}</span>
              </div>
              <div v-if="selectedNPCDetail.resistances.poison" class="info-row">
                <span class="info-label">Poison Resistance:</span>
                <span class="info-value">{{ selectedNPCDetail.resistances.poison }}</span>
              </div>
            </div>
          </div>

          <!-- Spawn Locations -->
          <div v-if="selectedNPCDetail.spawn_locations && selectedNPCDetail.spawn_locations.length > 0" class="detail-section">
            <h4>This NPC spawns in</h4>
            <div class="spawn-locations">
              <div v-for="location in selectedNPCDetail.spawn_locations" :key="location.zone_short_name" class="spawn-location">
                <strong>{{ location.zone_long_name || location.zone_short_name }}</strong>
              </div>
            </div>
          </div>

          <!-- NPC Spells -->
          <div v-if="selectedNPCDetail.spells && selectedNPCDetail.spells.length > 0" class="detail-section">
            <h4>Spells cast by this NPC</h4>
            <div class="npc-spells">
              <div v-for="spell in selectedNPCDetail.spells" :key="spell.spell_id" class="spell-item">
                <div class="spell-item-info">
                  <img 
                    v-if="spell.icon" 
                    :src="`/icons/spells/${spell.icon}.gif`" 
                    :alt="spell.spell_name"
                    @error="handleIconError"
                    class="spell-item-icon"
                  />
                  <i v-else class="fas fa-magic spell-item-icon-placeholder"></i>
                  <div class="spell-details">
                    <span class="spell-name">{{ spell.spell_name }}</span>
                    <div class="spell-meta">
                      <span v-if="spell.priority" class="spell-priority">Priority: {{ spell.priority }}</span>
                      <span v-if="spell.recast_delay" class="spell-recast">Recast: {{ spell.recast_delay }}s</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Merchant Items -->
          <div v-if="selectedNPCDetail.merchant_items && selectedNPCDetail.merchant_items.length > 0" class="detail-section">
            <h4>Items sold by this merchant</h4>
            <div class="merchant-items">
              <div v-for="item in selectedNPCDetail.merchant_items" :key="item.item_id" class="merchant-item">
                <div class="merchant-item-info">
                  <img 
                    v-if="item.icon" 
                    :src="`/icons/items/${item.icon}.gif`" 
                    :alt="item.item_name"
                    @error="handleIconError"
                    class="merchant-item-icon"
                  />
                  <i v-else class="fas fa-cube merchant-item-icon-placeholder"></i>
                  <div class="merchant-details">
                    <span class="merchant-item-name">{{ item.item_name }}</span>
                    <span v-if="item.price" class="merchant-price">{{ item.price?.toLocaleString() }} copper</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Loot Drops (if any) -->
          <div v-if="selectedNPCDetail.loot_drops && selectedNPCDetail.loot_drops.length > 0" class="detail-section">
            <h4>When killed, this NPC drops</h4>
            <div class="loot-drops">
              <div v-for="drop in selectedNPCDetail.loot_drops" :key="drop.item_id" class="loot-item">
                <div class="loot-item-info">
                  <img 
                    v-if="drop.icon" 
                    :src="`/icons/items/${drop.icon}.gif`" 
                    :alt="drop.item_name"
                    @error="handleIconError"
                    class="loot-item-icon"
                  />
                  <i v-else class="fas fa-cube loot-item-icon-placeholder"></i>
                  <span class="loot-item-name">{{ drop.item_name }}</span>
                  <span class="loot-probability">{{ drop.probability }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast Notifications -->
    <div class="toast-container">
      <div v-for="toast in toasts" :key="toast.id" class="toast" :class="toast.type">
        <i :class="getToastIcon(toast.type)"></i>
        <div class="toast-content">
          <div class="toast-title">{{ toast.title }}</div>
          <div v-if="toast.message" class="toast-message">{{ toast.message }}</div>
        </div>
        <button @click="removeToast(toast.id)" class="toast-close">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import LoadingModal from '../components/LoadingModal.vue'

// API configuration
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 
  (import.meta.env.PROD ? 'https://eqdatascraper-backend-production.up.railway.app' : '')

export default {
  name: 'NPCs',
  components: {
    LoadingModal
  },
  
  data() {
    return {
      // Search state
      searchQuery: '',
      searching: false,
      searchPerformed: false,
      searchResults: [],
      totalCount: 0,
      
      // View mode
      viewMode: 'list', // Default to list view like Items and Spells
      
      // Pagination
      currentPage: 1,
      limit: 20,
      paginating: false,
      
      // Filters
      minLevel: '',
      maxLevel: '',
      selectedZone: '',
      
      // NPC details modal
      selectedNPCDetail: null,
      loadingNPCDetails: false,
      
      // Toast notifications
      toasts: [],
      
      // EverQuest data mappings
      raceNames: {
        1: 'Human', 2: 'Barbarian', 3: 'Erudite', 4: 'Wood Elf', 5: 'High Elf', 6: 'Dark Elf',
        7: 'Half Elf', 8: 'Dwarf', 9: 'Troll', 10: 'Ogre', 11: 'Halfling', 12: 'Gnome',
        128: 'Iksar', 130: 'Vah Shir', 330: 'Froglok', 522: 'Drakkin'
      },
      
      classNames: {
        1: 'Warrior', 2: 'Cleric', 3: 'Paladin', 4: 'Ranger', 5: 'Shadow Knight', 6: 'Druid',
        7: 'Monk', 8: 'Bard', 9: 'Rogue', 10: 'Shaman', 11: 'Necromancer', 12: 'Wizard',
        13: 'Magician', 14: 'Enchanter', 15: 'Beastlord', 16: 'Berserker'
      }
    }
  },
  
  computed: {
    totalPages() {
      return Math.ceil(this.totalCount / this.limit)
    },
    
    hasResistances() {
      if (!this.selectedNPCDetail || !this.selectedNPCDetail.resistances) return false
      const res = this.selectedNPCDetail.resistances
      return res.magic || res.cold || res.disease || res.fire || res.poison
    }
  },
  
  methods: {
    async performSearch() {
      if (!this.searchQuery.trim() && !this.minLevel && !this.maxLevel && !this.selectedZone) {
        this.showToast('Search Required', 'Please enter a search term or select filters.', 'warning')
        return
      }

      this.searching = true
      this.currentPage = 1
      
      try {
        const params = {
          q: this.searchQuery.trim(),
          limit: this.limit,
          offset: 0
        }
        
        // Add filters
        if (this.minLevel) params.min_level = this.minLevel
        if (this.maxLevel) params.max_level = this.maxLevel
        if (this.selectedZone) params.zone = this.selectedZone
        
        const response = await axios.get(`${API_BASE_URL}/api/npcs/search`, { params })
        
        this.searchResults = response.data.npcs || []
        this.totalCount = response.data.total_count || 0
        this.searchPerformed = true
        
      } catch (error) {
        console.error('Error searching NPCs:', error)
        this.showToast('Search Error', 'Failed to search NPCs. Please try again.', 'error')
        this.searchResults = []
        this.totalCount = 0
        this.searchPerformed = true
      } finally {
        this.searching = false
      }
    },

    async goToPage(page) {
      if (page === this.currentPage || page < 1 || page > this.totalPages) return
      
      this.paginating = true
      this.currentPage = page
      
      try {
        const params = {
          q: this.searchQuery.trim(),
          limit: this.limit,
          offset: (page - 1) * this.limit
        }
        
        // Add filters
        if (this.minLevel) params.min_level = this.minLevel
        if (this.maxLevel) params.max_level = this.maxLevel
        if (this.selectedZone) params.zone = this.selectedZone
        
        const response = await axios.get(`${API_BASE_URL}/api/npcs/search`, { params })
        this.searchResults = response.data.npcs || []
        
      } catch (error) {
        console.error('Error loading page:', error)
        this.showToast('Loading Error', 'Failed to load page. Please try again.', 'error')
      } finally {
        this.paginating = false
      }
    },

    clearFilters() {
      this.minLevel = ''
      this.maxLevel = ''
      this.selectedZone = ''
    },

    async openNPCModal(npc) {
      try {
        // Disable body scrolling
        document.body.style.overflow = 'hidden'
        
        // Start loading state
        this.loadingNPCDetails = true
        
        // Fetch detailed NPC information
        const response = await axios.get(`${API_BASE_URL}/api/npcs/${npc.id}/details`)
        
        // Combine basic NPC data with detailed information
        this.selectedNPCDetail = { ...npc, ...response.data }
        
        // Stop loading state
        this.loadingNPCDetails = false
        
      } catch (error) {
        console.error('Error fetching NPC details:', error)
        this.selectedNPCDetail = { ...npc }
        this.loadingNPCDetails = false
        this.showToast('Loading Error', 'Failed to load NPC details.', 'error')
      }
    },

    closeNPCModal() {
      this.selectedNPCDetail = null
      this.loadingNPCDetails = false
      // Re-enable body scrolling
      document.body.style.overflow = ''
    },

    getRaceName(raceId) {
      return this.raceNames[raceId] || `Race ${raceId}`
    },

    getClassName(classId) {
      return this.classNames[classId] || `Class ${classId}`
    },

    getFormattedZoneName(npc) {
      // Use long name if available, otherwise format short name
      if (npc.zone_long_name && npc.zone_long_name.trim()) {
        return npc.zone_long_name
      }
      
      // Format short name: remove underscores, capitalize words
      if (npc.zone_short_name) {
        return npc.zone_short_name
          .replace(/_/g, ' ')
          .split(' ')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
          .join(' ')
      }
      
      return 'Unknown Zone'
    },

    handleIconError(event) {
      event.target.style.display = 'none'
    },

    // Toast notification methods
    showToast(title, message = '', type = 'info') {
      const id = Date.now() + Math.random()
      this.toasts.push({ id, title, message, type })
      
      // Auto-remove after 5 seconds
      setTimeout(() => {
        this.removeToast(id)
      }, 5000)
    },

    removeToast(id) {
      const index = this.toasts.findIndex(t => t.id === id)
      if (index > -1) {
        this.toasts.splice(index, 1)
      }
    },

    getToastIcon(type) {
      switch (type) {
        case 'success': return 'fa-check-circle'
        case 'error': return 'fa-exclamation-circle'
        case 'warning': return 'fa-exclamation-triangle'
        case 'info': return 'fa-info-circle'
        default: return 'fa-info-circle'
      }
    }
  },

  unmounted() {
    // Ensure body scrolling is restored if component is destroyed while modal is open
    document.body.style.overflow = ''
  }
}
</script>

<style scoped>
/* Use the same styling patterns as Items.vue and Spells.vue */
.npcs-page {
  padding: 20px;
  padding-top: 100px; /* Prevent logo overlap */
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  font-size: 3rem;
  margin: 0 0 15px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 1.2rem;
  color: #888;
  margin: 0;
}

/* Search Section */
.search-section {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 30px;
  margin-bottom: 30px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.search-container {
  max-width: 800px;
  margin: 0 auto;
}

.search-input-group {
  display: flex;
  gap: 15px;
  margin-bottom: 25px;
}

.search-input {
  flex: 1;
  padding: 15px 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 1rem;
  backdrop-filter: blur(5px);
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.7);
}

.search-button {
  padding: 15px 25px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.search-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
}

.search-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.filters-container {
  display: flex;
  gap: 20px;
  align-items: end;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group label {
  color: white;
  font-weight: 500;
  font-size: 0.9rem;
}

.filter-input, .filter-select {
  padding: 10px 15px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  backdrop-filter: blur(5px);
  min-width: 120px;
}

.filter-select option {
  background: #2a2a2a;
  color: white;
}

.clear-filters-button {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.clear-filters-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Results Section */
.results-section {
  margin-top: 30px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 25px;
  gap: 20px;
}

.results-info-container h2 {
  color: white;
  margin: 0 0 10px 0;
  font-size: 1.8rem;
}

.results-info {
  color: #9ca3af;
  font-size: 0.95rem;
}

.results-info span:not(:last-child) {
  margin-right: 8px;
}

/* View Toggle */
.view-toggle-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-toggle-label {
  color: #9ca3af;
  font-weight: 500;
  font-size: 0.95rem;
}

.view-toggle {
  display: flex;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
  padding: 4px;
  gap: 4px;
}

.view-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.view-button:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.view-button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.view-button-text {
  font-weight: 500;
}

/* NPC List View */
.npc-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 30px;
}

.npc-row {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.12) 0%, 
    rgba(255, 255, 255, 0.08) 100%);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 16px;
  padding: 20px 26px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  position: relative;
  overflow: hidden;
}

.npc-row::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.05) 0%, 
    rgba(118, 75, 162, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.4s ease;
}

.npc-row:hover {
  transform: translateY(-3px) scale(1.01);
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(102, 126, 234, 0.3);
  border-color: rgba(102, 126, 234, 0.6);
}

.npc-row:hover::before {
  opacity: 1;
}

.npc-main-info {
  flex: 1;
  min-width: 0;
  z-index: 1;
}

.npc-name-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.npc-row .npc-name {
  color: #f8fafc;
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  line-height: 1.2;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.2px;
}

.npc-details {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.9rem;
}

.npc-level {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 14px;
  font-size: 0.8rem;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.npc-separator {
  color: #64748b;
  font-weight: 600;
  font-size: 0.7rem;
}

.npc-race {
  color: #94a3b8;
  font-weight: 600;
  font-size: 0.88rem;
}

.npc-class {
  color: #cbd5e1;
  font-weight: 600;
  font-size: 0.88rem;
}

.npc-zone-display {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-width: 140px;
  z-index: 1;
}

.zone-name {
  color: #e2e8f0;
  font-size: 0.95rem;
  font-weight: 600;
  text-align: right;
  line-height: 1.3;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  padding: 6px 14px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(8px);
}

/* NPC Grid View */
.npc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.npc-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.npc-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
  border-color: rgba(102, 126, 234, 0.5);
}

.npc-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.npc-name {
  color: white;
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
}

.npc-level {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 15px;
  font-size: 0.85rem;
  font-weight: 600;
}

.npc-card-body {
  color: #ccc;
}

.npc-info {
  display: flex;
  gap: 15px;
  margin-bottom: 10px;
}

.npc-race, .npc-class {
  font-weight: 500;
}

.npc-stats {
  display: flex;
  gap: 15px;
  margin-bottom: 10px;
}

.npc-hp, .npc-damage {
  font-size: 0.9rem;
}

.npc-zone {
  font-size: 0.85rem;
  opacity: 0.8;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(5px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.npc-modal {
  background: rgba(30, 30, 30, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 25px 30px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.npc-header-info h3 {
  color: white;
  margin: 0 0 10px 0;
  font-size: 1.8rem;
}

.npc-header-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.npc-id-badge, .level-badge, .race-badge, .class-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  color: #ccc;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 10px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.modal-body {
  padding: 30px;
}

.detail-section {
  margin-bottom: 30px;
}

.detail-section h4 {
  color: white;
  margin: 0 0 15px 0;
  font-size: 1.3rem;
  border-bottom: 2px solid rgba(102, 126, 234, 0.5);
  padding-bottom: 8px;
}

.info-grid {
  display: grid;
  gap: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.info-label {
  color: #ccc;
  font-weight: 500;
  min-width: 150px;
}

.info-value {
  color: white;
  font-weight: 400;
  text-align: right;
}

.spawn-locations, .loot-drops {
  display: grid;
  gap: 10px;
}

.spawn-location {
  background: rgba(255, 255, 255, 0.05);
  padding: 12px 15px;
  border-radius: 8px;
  color: #ccc;
}

.loot-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 12px 15px;
}

.loot-item-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.loot-item-icon {
  width: 24px;
  height: 24px;
  image-rendering: pixelated;
}

.loot-item-icon-placeholder {
  width: 24px;
  height: 24px;
  color: #666;
}

.loot-item-name {
  flex: 1;
  color: white;
  font-weight: 500;
}

.loot-probability {
  color: #ccc;
  font-size: 0.9rem;
}

/* NPC Spells */
.npc-spells {
  display: grid;
  gap: 10px;
}

.spell-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 12px 15px;
}

.spell-item-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.spell-item-icon {
  width: 24px;
  height: 24px;
  image-rendering: pixelated;
}

.spell-item-icon-placeholder {
  width: 24px;
  height: 24px;
  color: #666;
}

.spell-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.spell-name {
  color: white;
  font-weight: 500;
}

.spell-meta {
  display: flex;
  gap: 15px;
  font-size: 0.85rem;
  color: #ccc;
}

.spell-priority, .spell-recast {
  color: #ccc;
}

/* Merchant Items */
.merchant-items {
  display: grid;
  gap: 10px;
}

.merchant-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 12px 15px;
}

.merchant-item-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.merchant-item-icon {
  width: 24px;
  height: 24px;
  image-rendering: pixelated;
}

.merchant-item-icon-placeholder {
  width: 24px;
  height: 24px;
  color: #666;
}

.merchant-details {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.merchant-item-name {
  color: white;
  font-weight: 500;
}

.merchant-price {
  color: #ffd700;
  font-weight: 600;
  font-size: 0.9rem;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 30px;
}

.pagination-button {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 10px 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.pagination-button:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
}

.pagination-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-info {
  color: #ccc;
  padding: 0 15px;
  font-weight: 500;
}

/* No Results */
.no-results {
  text-align: center;
  padding: 60px 20px;
  color: #ccc;
}

.no-results-content i {
  font-size: 4rem;
  margin-bottom: 20px;
  opacity: 0.5;
}

.no-results-content h3 {
  margin: 0 0 10px 0;
  color: white;
}

/* Toast Notifications */
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toast {
  background: rgba(30, 30, 30, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 15px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 300px;
  max-width: 400px;
  color: white;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
  animation: slideInRight 0.3s ease;
}

.toast.success { border-left: 4px solid #10b981; }
.toast.error { border-left: 4px solid #ef4444; }
.toast.warning { border-left: 4px solid #f59e0b; }
.toast.info { border-left: 4px solid #3b82f6; }

.toast-content {
  flex: 1;
}

.toast-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.toast-message {
  font-size: 0.9rem;
  opacity: 0.8;
}

.toast-close {
  background: none;
  border: none;
  color: #ccc;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.toast-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .npcs-page {
    padding: 15px;
    padding-top: 80px;
  }
  
  .page-header h1 {
    font-size: 2rem;
  }
  
  .search-input-group {
    flex-direction: column;
  }
  
  .filters-container {
    flex-direction: column;
    align-items: stretch;
  }
  
  .results-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .view-toggle-container {
    align-self: stretch;
    justify-content: center;
  }
  
  .view-button-text {
    display: inline;
  }
  
  .npc-grid {
    grid-template-columns: 1fr;
  }
  
  .npc-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
    padding: 18px 22px;
  }
  
  .npc-zone-display {
    align-self: stretch;
    justify-content: flex-start;
    min-width: auto;
  }
  
  .zone-name {
    text-align: left;
  }
  
  .modal-overlay {
    padding: 10px;
  }
  
  .modal-header, .modal-body {
    padding: 20px;
  }
  
  .npc-header-meta {
    flex-direction: column;
    align-items: start;
  }
  
  .info-row {
    flex-direction: column;
    align-items: start;
    gap: 4px;
  }
  
  .info-value {
    text-align: left;
  }
}
</style>