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
        <h2>Search Results</h2>
        <div class="results-meta">
          <span class="results-count">
            Found {{ totalCount.toLocaleString() }} NPC{{ totalCount !== 1 ? 's' : '' }}
          </span>
          <span v-if="searchQuery" class="search-query">
            for "{{ searchQuery }}"
          </span>
        </div>
      </div>

      <!-- Results List -->
      <div v-if="searchResults.length > 0" class="npc-results">
        <div class="npc-grid">
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
                <span v-if="npc.damage" class="npc-damage">
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
              <div v-if="selectedNPCDetail.faction_id" class="info-row">
                <span class="info-label">Main Faction:</span>
                <span class="info-value">{{ selectedNPCDetail.faction_name || `Faction ${selectedNPCDetail.faction_id}` }}</span>
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
              <div v-if="selectedNPCDetail.mindmg || selectedNPCDetail.maxdmg" class="info-row">
                <span class="info-label">Damage:</span>
                <span class="info-value">{{ selectedNPCDetail.mindmg }} to {{ selectedNPCDetail.maxdmg }}</span>
              </div>
              <div v-if="selectedNPCDetail.attack_speed" class="info-row">
                <span class="info-label">Attack Speed:</span>
                <span class="info-value">{{ selectedNPCDetail.attack_speed }}%</span>
              </div>
              <div v-if="selectedNPCDetail.special_attacks" class="info-row">
                <span class="info-label">Special Attacks:</span>
                <span class="info-value">{{ getSpecialAttacks(selectedNPCDetail.special_attacks) }}</span>
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

    getSpecialAttacks(specialAttacks) {
      if (!specialAttacks || specialAttacks === '0') return 'None'
      // This would need to be expanded based on EQEmu's special attack flags
      return 'Various'
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
  margin-bottom: 25px;
}

.results-header h2 {
  color: white;
  margin: 0 0 10px 0;
  font-size: 1.8rem;
}

.results-meta {
  color: #ccc;
  font-size: 1rem;
}

.results-count {
  font-weight: 600;
}

.search-query {
  font-style: italic;
  opacity: 0.8;
}

/* NPC Grid */
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
  
  .npc-grid {
    grid-template-columns: 1fr;
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