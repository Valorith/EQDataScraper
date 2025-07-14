<template>
  <div class="spells-page">
    <div class="page-header">
      <h1>Spell Database</h1>
      <p class="subtitle">Search and explore spells from the database</p>
    </div>

    <!-- Search Section -->
    <div class="search-section">
      <div class="search-container">
        <div class="search-input-group">
          <input
            v-model="searchQuery"
            @keyup.enter="performSearch()"
            type="text"
            placeholder="Search spells by name..."
            class="search-input"
          />
          <button @click="performSearch()" class="search-button" :disabled="searching">
            <i :class="searching ? 'fas fa-spinner fa-spin' : 'fas fa-search'"></i>
            <span class="search-button-text">{{ searching ? 'Searching...' : 'Search' }}</span>
          </button>
        </div>
        
        <!-- Basic Filters -->
        <div class="filters-container">
          <div class="filter-group">
            <label for="class-filter">Class:</label>
            <select id="class-filter" v-model="selectedClass" class="filter-select">
              <option value="">All Classes</option>
              <option value="warrior">Warrior</option>
              <option value="cleric">Cleric</option>
              <option value="paladin">Paladin</option>
              <option value="ranger">Ranger</option>
              <option value="shadowknight">Shadow Knight</option>
              <option value="druid">Druid</option>
              <option value="monk">Monk</option>
              <option value="bard">Bard</option>
              <option value="rogue">Rogue</option>
              <option value="shaman">Shaman</option>
              <option value="necromancer">Necromancer</option>
              <option value="wizard">Wizard</option>
              <option value="magician">Magician</option>
              <option value="enchanter">Enchanter</option>
              <option value="beastlord">Beastlord</option>
              <option value="berserker">Berserker</option>
            </select>
          </div>
          
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
            <label for="skill-filter">Skill:</label>
            <select id="skill-filter" v-model="selectedSkill" class="filter-select">
              <option value="">All Skills</option>
              <option value="0">Conjuration</option>
              <option value="1">Divination</option>
              <option value="2">Abjuration</option>
              <option value="3">Alteration</option>
              <option value="4">Evocation</option>
              <option value="5">Singing</option>
              <option value="6">Percussion</option>
              <option value="7">Stringed</option>
              <option value="8">Brass</option>
              <option value="9">Wind</option>
            </select>
          </div>
          
          <button @click="clearFilters" class="clear-filters-button">
            <i class="fas fa-times"></i>
            Clear Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Results Section -->
    <div class="results-section">
      <!-- Results Header -->
      <div class="results-header">
        <div class="results-info">
          <span v-if="searchResults.length > 0">
            Showing {{ searchResults.length }} of {{ totalCount }} spells
          </span>
          <span v-else-if="!searching && searchPerformed">
            No spells found
          </span>
          <span v-else>
            Enter a search term to find spells
          </span>
        </div>
        
        <!-- View Toggle -->
        <div class="view-toggle">
          <button 
            @click="viewMode = 'grid'" 
            :class="['view-toggle-button', { active: viewMode === 'grid' }]"
            title="Grid View"
          >
            <i class="fas fa-th"></i>
          </button>
          <button 
            @click="viewMode = 'list'" 
            :class="['view-toggle-button', { active: viewMode === 'list' }]"
            title="List View"
          >
            <i class="fas fa-list"></i>
          </button>
        </div>
      </div>

      <!-- Spell Results -->
      <div v-if="searchResults.length > 0" :class="['spell-results', viewMode]">
        <div v-for="spell in searchResults" :key="spell.spell_id" class="spell-card">
          <div class="spell-header">
            <h3 class="spell-name">{{ spell.name }}</h3>
            <div class="spell-meta">
              <span class="spell-id">ID: {{ spell.spell_id }}</span>
            </div>
          </div>
          
          <div class="spell-details">
            <div class="spell-detail-row">
              <span class="detail-label">Mana:</span>
              <span class="detail-value">{{ spell.mana || 'N/A' }}</span>
            </div>
            
            <div class="spell-detail-row">
              <span class="detail-label">Cast Time:</span>
              <span class="detail-value">{{ formatCastTime(spell.cast_time) }}</span>
            </div>
            
            <div class="spell-detail-row">
              <span class="detail-label">Range:</span>
              <span class="detail-value">{{ spell.range || 'N/A' }}</span>
            </div>
            
            <div class="spell-detail-row">
              <span class="detail-label">Duration:</span>
              <span class="detail-value">{{ formatDuration(spell.buffduration) }}</span>
            </div>
          </div>
          
          <!-- Class Level Requirements -->
          <div class="spell-class-levels">
            <div class="class-levels-header">Class Level Requirements:</div>
            <div class="class-levels-grid">
              <div 
                v-for="(level, className) in spell.class_levels" 
                :key="className"
                :class="['class-level', { 'available': level && level !== 255 }]"
                :title="`${className}: ${level === 255 ? 'Cannot use' : level}`"
              >
                <span class="class-name">{{ className.charAt(0).toUpperCase() + className.slice(1) }}</span>
                <span class="class-level-value">{{ level === 255 ? '-' : level }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalCount > limit" class="pagination">
        <button 
          @click="goToPage(currentPage - 1)" 
          :disabled="currentPage === 1"
          class="pagination-button"
        >
          <i class="fas fa-chevron-left"></i>
          Previous
        </button>
        
        <span class="pagination-info">
          Page {{ currentPage }} of {{ totalPages }}
        </span>
        
        <button 
          @click="goToPage(currentPage + 1)" 
          :disabled="currentPage === totalPages"
          class="pagination-button"
        >
          Next
          <i class="fas fa-chevron-right"></i>
        </button>
      </div>
    </div>

    <!-- Loading Modal -->
    <div v-if="searching" class="loading-modal">
      <div class="loading-content">
        <i class="fas fa-spinner fa-spin loading-icon"></i>
        <p>Searching spells...</p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Spells',
  data() {
    return {
      searchQuery: '',
      searchResults: [],
      totalCount: 0,
      searching: false,
      searchPerformed: false,
      viewMode: 'grid',
      
      // Pagination
      currentPage: 1,
      limit: 20,
      
      // Basic filters
      selectedClass: '',
      minLevel: '',
      maxLevel: '',
      selectedSkill: '',
      
      // API configuration
      API_BASE_URL: import.meta.env.VITE_BACKEND_URL || 
        (import.meta.env.PROD ? 'https://eqdatascraper-backend-production.up.railway.app' : '')
    }
  },
  
  computed: {
    totalPages() {
      return Math.ceil(this.totalCount / this.limit)
    },
    
    offset() {
      return (this.currentPage - 1) * this.limit
    }
  },
  
  methods: {
    async performSearch() {
      if (!this.searchQuery.trim() && !this.hasActiveFilters()) {
        alert('Please enter a search term or apply filters')
        return
      }
      
      this.searching = true
      this.searchPerformed = true
      
      try {
        // Build query parameters
        const params = new URLSearchParams()
        
        if (this.searchQuery.trim()) {
          params.append('q', this.searchQuery.trim())
        }
        
        params.append('limit', this.limit.toString())
        params.append('offset', this.offset.toString())
        
        // Add basic filters
        const filters = this.buildFilters()
        if (filters.length > 0) {
          params.append('filters', JSON.stringify(filters))
        }
        
        console.log('Searching with params:', params.toString())
        
        const response = await axios.get(`${this.API_BASE_URL}/api/spells/search?${params.toString()}`)
        
        // Check if API returned HTML instead of JSON (proxy routing issue)
        if (typeof response.data === 'string' && response.data.includes('<!DOCTYPE html>')) {
          throw new Error('API returned HTML instead of JSON - possible proxy routing issue')
        }
        
        this.searchResults = response.data.spells || []
        this.totalCount = response.data.total_count || 0
        
        console.log(`Found ${this.searchResults.length} spells (${this.totalCount} total)`)
        
      } catch (error) {
        console.error('Search error:', error)
        alert('Search failed: ' + (error.response?.data?.error || error.message))
        this.searchResults = []
        this.totalCount = 0
      } finally {
        this.searching = false
      }
    },
    
    buildFilters() {
      const filters = []
      
      // Class filter
      if (this.selectedClass) {
        filters.push({
          field: `${this.selectedClass}_level`,
          operator: 'class_can_use',
          value: true
        })
      }
      
      // Level range filters
      if (this.minLevel) {
        // For class-specific level filtering, we need to handle this differently
        // For now, we'll skip this and implement it in advanced filters
      }
      
      // Skill filter
      if (this.selectedSkill) {
        filters.push({
          field: 'skill',
          operator: 'equals',
          value: parseInt(this.selectedSkill)
        })
      }
      
      return filters
    },
    
    hasActiveFilters() {
      return this.selectedClass || this.minLevel || this.maxLevel || this.selectedSkill
    },
    
    clearFilters() {
      this.selectedClass = ''
      this.minLevel = ''
      this.maxLevel = ''
      this.selectedSkill = ''
      this.currentPage = 1
      
      // Perform search again if we had results
      if (this.searchQuery.trim()) {
        this.performSearch()
      }
    },
    
    goToPage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page
        this.performSearch()
      }
    },
    
    formatCastTime(castTime) {
      if (!castTime || castTime === 0) return 'Instant'
      return `${(castTime / 1000).toFixed(1)}s`
    },
    
    formatDuration(duration) {
      if (!duration || duration === 0) return 'Instant'
      if (duration === 65535) return 'Permanent'
      
      const minutes = Math.floor(duration / 60)
      const seconds = duration % 60
      
      if (minutes > 0) {
        return seconds > 0 ? `${minutes}m ${seconds}s` : `${minutes}m`
      } else {
        return `${seconds}s`
      }
    }
  }
}
</script>

<style scoped>
.spells-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 2.5em;
  color: #333;
  margin-bottom: 10px;
}

.subtitle {
  color: #666;
  font-size: 1.1em;
}

.search-section {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 25px;
  margin-bottom: 30px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.search-input-group {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.9);
}

.search-button {
  padding: 12px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.2s;
}

.search-button:hover:not(:disabled) {
  background: #0056b3;
}

.search-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.filters-container {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  align-items: end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.filter-group label {
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.filter-select,
.filter-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.9);
  min-width: 120px;
}

.clear-filters-button {
  padding: 8px 12px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: background-color 0.2s;
}

.clear-filters-button:hover {
  background: #c82333;
}

.results-section {
  margin-top: 30px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.results-info {
  font-size: 16px;
  color: #666;
}

.view-toggle {
  display: flex;
  gap: 5px;
}

.view-toggle-button {
  padding: 8px 12px;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.view-toggle-button.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.spell-results.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.spell-results.list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.spell-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: transform 0.2s, box-shadow 0.2s;
}

.spell-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.spell-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 15px;
}

.spell-name {
  font-size: 1.3em;
  color: #333;
  margin: 0;
}

.spell-meta {
  text-align: right;
  font-size: 0.9em;
  color: #666;
}

.spell-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 15px;
}

.spell-detail-row {
  display: flex;
  justify-content: space-between;
}

.detail-label {
  font-weight: 500;
  color: #555;
}

.detail-value {
  color: #333;
}

.spell-class-levels {
  border-top: 1px solid rgba(255, 255, 255, 0.3);
  padding-top: 15px;
}

.class-levels-header {
  font-weight: 500;
  color: #333;
  margin-bottom: 10px;
  font-size: 0.9em;
}

.class-levels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 5px;
}

.class-level {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.1);
  font-size: 0.8em;
}

.class-level.available {
  background: rgba(0, 123, 255, 0.1);
  color: #007bff;
}

.class-name {
  font-size: 0.75em;
  opacity: 0.8;
}

.class-level-value {
  font-weight: 500;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 30px;
}

.pagination-button {
  padding: 10px 15px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: background-color 0.2s;
}

.pagination-button:hover:not(:disabled) {
  background: #0056b3;
}

.pagination-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.pagination-info {
  font-weight: 500;
  color: #333;
}

.loading-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loading-content {
  background: white;
  padding: 30px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.loading-icon {
  font-size: 2em;
  color: #007bff;
  margin-bottom: 15px;
}

/* Responsive design */
@media (max-width: 768px) {
  .filters-container {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-group {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
  
  .spell-results.grid {
    grid-template-columns: 1fr;
  }
  
  .results-header {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
  }
  
  .spell-details {
    grid-template-columns: 1fr;
  }
}
</style>