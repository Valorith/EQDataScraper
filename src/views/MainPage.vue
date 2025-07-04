<template>
  <div class="main-container">
    <div class="hero-section">
      <div class="hero-content">
        <h1 class="main-title">Clumsy's World</h1>
        <p class="main-subtitle">Information Compendium</p>
      </div>
      
    </div>
    
    <!-- Global Search -->
    <div class="global-search-container">
      <div class="search-input-wrapper">
        <input
          ref="searchInput"
          v-model="searchQuery"
          @input="handleSearchInput"
          @focus="showDropdown = true"
          @keydown="handleKeyDown"
          type="text"
          placeholder="Search across all content..."
          class="global-search-input"
          autocomplete="off"
        />
        <div class="search-icon">🔍</div>
        <button 
          v-if="searchQuery" 
          @click="clearSearch" 
          class="clear-search-btn"
        >
          ×
        </button>
        
        <!-- Search Results Dropdown -->
        <div v-if="showDropdown && searchResults.length > 0" :class="['search-dropdown', showPagination ? 'has-pagination' : 'no-pagination']">
          <div class="search-results-header">
            <span>{{ searchResults.length }} result{{ searchResults.length === 1 ? '' : 's' }}</span>
            <span v-if="showPagination" class="page-indicator">
              Page {{ currentPage + 1 }} of {{ totalPages }}
            </span>
          </div>
          <div class="search-results-list">
            <div 
              v-for="(spell, index) in paginatedResults" 
              :key="`${spell.spell_id}-${spell.classes.join('-')}`"
              :class="['search-result-item', { 'highlighted': index === selectedIndex }]"
              @click="selectSpell(spell)"
              @mouseenter="selectedIndex = index"
            >
              <div class="search-result-info">
                <img 
                  v-if="spell.icon" 
                  :src="spell.icon" 
                  :alt="`${spell.name} icon`"
                  class="search-result-icon"
                  @error="handleIconError"
                />
                <div class="search-result-text">
                  <div class="search-result-name" v-html="highlightMatch(spell.name)"></div>
                  <div class="search-result-details">
                    Level {{ spell.level }}
                    <span v-if="spell.mana"> • {{ spell.mana }} MP</span>
                    <span class="spell-classes"> • {{ spell.classes.join(', ') }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-if="showPagination" class="search-results-footer">
            <div class="pagination-info">
              <div>Showing {{ (currentPage * resultsPerPage) + 1 }}-{{ Math.min((currentPage + 1) * resultsPerPage, searchResults.length) }} of {{ searchResults.length }}</div>
              <div class="keyboard-tip">Tip: Use tab and keyboard arrows to navigate. Enter to select.</div>
            </div>
            <div class="pagination-controls">
              <button 
                @click="goToPreviousPage" 
                :disabled="!canGoToPreviousPage"
                class="pagination-arrow"
                title="Previous page"
              >
                ←
              </button>
              <button 
                @click="goToNextPage" 
                :disabled="!canGoToNextPage"
                :class="['pagination-arrow', { 'glow-attention': showRightArrowGlow }]"
                title="Next page"
              >
                →
              </button>
            </div>
          </div>
        </div>
        
        <!-- Empty State -->
        <div v-if="showDropdown && searchQuery && searchResults.length === 0 && !searchLoading" class="search-empty">
          No content found matching "{{ searchQuery }}"
        </div>
        
        <!-- Loading State -->
        <div v-if="searchLoading" class="search-loading">
          <div class="search-spinner"></div>
          <span>Searching...</span>
        </div>
      </div>
    </div>
    
    <!-- Navigation Menu -->
    <div class="navigation-grid">
      <router-link 
        to="/spells"
        class="nav-card spells-nav"
      >
        <div class="nav-icon">
          <div class="nav-icon-symbol">✨</div>
        </div>
        <div class="nav-content">
          <h3 class="nav-title">Spells</h3>
          <p class="nav-description">Browse spells by class, view detailed information, and manage your spell collection</p>
        </div>
      </router-link>
      
      <div class="nav-card items-nav placeholder">
        <div class="nav-icon">
          <div class="nav-icon-symbol">⚔️</div>
        </div>
        <div class="nav-content">
          <h3 class="nav-title">Items</h3>
          <p class="nav-description">Explore weapons, armor, and magical items (Coming Soon)</p>
        </div>
        <div class="coming-soon-badge">Coming Soon</div>
      </div>
      
      <div class="nav-card wiki-nav placeholder">
        <div class="nav-icon">
          <div class="nav-icon-symbol">📚</div>
        </div>
        <div class="nav-content">
          <h3 class="nav-title">Wiki</h3>
          <p class="nav-description">Comprehensive game guides and information (Coming Soon)</p>
        </div>
        <div class="coming-soon-badge">Coming Soon</div>
      </div>
      
      <div class="nav-card zones-nav placeholder">
        <div class="nav-icon">
          <div class="nav-icon-symbol">🗺️</div>
        </div>
        <div class="nav-content">
          <h3 class="nav-title">Zones</h3>
          <p class="nav-description">Explore different zones and their contents (Coming Soon)</p>
        </div>
        <div class="coming-soon-badge">Coming Soon</div>
      </div>
      
      <div class="nav-card raid-nav placeholder">
        <div class="nav-icon">
          <div class="nav-icon-symbol">🏰</div>
        </div>
        <div class="nav-content">
          <h3 class="nav-title">Raid Management</h3>
          <p class="nav-description">A comprehensive raid and loot management tool for guilds (Coming Soon)</p>
        </div>
        <div class="coming-soon-badge">Coming Soon</div>
      </div>
    </div>
    
  </div>
</template>

<script>
import axios from 'axios'

// Configure API base URL
const API_BASE_URL = (() => {
  if (import.meta.env.PROD) {
    const envUrl = import.meta.env.VITE_BACKEND_URL
    if (envUrl && !envUrl.includes('localhost') && !envUrl.includes('127.0.0.1')) {
      return envUrl
    }
    return 'https://eqdatascraper-backend-production.up.railway.app'
  }
  return import.meta.env.VITE_BACKEND_URL || 'http://localhost:5001'
})()

export default {
  name: 'MainPage',
  data() {
    return {
      searchQuery: '',
      searchResults: [],
      showDropdown: false,
      selectedIndex: -1,
      searchLoading: false,
      searchTimeout: null,
      currentPage: 0,
      resultsPerPage: 10,
      showRightArrowGlow: false
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.searchResults.length / this.resultsPerPage)
    },
    
    paginatedResults() {
      const start = this.currentPage * this.resultsPerPage
      const end = start + this.resultsPerPage
      return this.searchResults.slice(start, end)
    },
    
    showPagination() {
      return this.searchResults.length > this.resultsPerPage
    },
    
    canGoToPreviousPage() {
      return this.currentPage > 0
    },
    
    canGoToNextPage() {
      return this.currentPage < this.totalPages - 1
    }
  },
  async mounted() {
    document.addEventListener('click', this.handleOutsideClick)
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleOutsideClick)
    if (this.searchTimeout) {
      clearTimeout(this.searchTimeout)
    }
  },
  methods: {
    handleSearchInput() {
      if (this.searchQuery.trim().startsWith('/')) {
        this.searchResults = []
        this.showDropdown = false
        this.currentPage = 0
        this.searchLoading = false
        return
      }
      
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout)
      }
      
      this.searchTimeout = setTimeout(() => {
        this.performSearch()
      }, 300)
    },
    
    async performSearch() {
      if (!this.searchQuery || this.searchQuery.length < 2) {
        this.searchResults = []
        this.showDropdown = false
        this.currentPage = 0
        return
      }
      
      if (this.searchQuery.trim().startsWith('/')) {
        this.searchResults = []
        this.showDropdown = false
        this.currentPage = 0
        return
      }
      
      this.searchLoading = true
      
      try {
        const response = await axios.get(`${API_BASE_URL}/api/search-spells?q=${encodeURIComponent(this.searchQuery)}`)
        this.searchResults = response.data.results || []
        this.showDropdown = true
        this.selectedIndex = -1
        this.currentPage = 0
        
        if (this.searchResults.length > this.resultsPerPage) {
          this.$nextTick(() => {
            this.showRightArrowGlow = true
            setTimeout(() => {
              this.showRightArrowGlow = false
            }, 2000)
          })
        }
      } catch (error) {
        console.error('Search error:', error)
        this.searchResults = []
        this.currentPage = 0
      } finally {
        this.searchLoading = false
      }
    },
    
    selectSpell(spell) {
      if (spell.class_names && spell.class_names.length > 0) {
        const firstClass = spell.class_names[0].toLowerCase()
        this.$router.push({ 
          name: 'ClassSpells', 
          params: { className: firstClass },
          hash: `#spell-${spell.spell_id}`,
          query: { openModal: 'true' }
        })
      }
      this.clearSearch()
    },
    
    clearSearch() {
      this.searchQuery = ''
      this.searchResults = []
      this.showDropdown = false
      this.selectedIndex = -1
      this.currentPage = 0
    },
    
    handleKeyDown(event) {
      if (!this.showDropdown || this.searchResults.length === 0) {
        if (event.key === 'Enter' && this.searchQuery.trim().startsWith('/')) {
          event.preventDefault()
          
          const command = this.searchQuery.trim()
          
          if (command === '/debug') {
            this.toggleDebugPanel()
          }
          
          this.clearSearch()
          return
        }
        return
      }
      
      const maxIndex = Math.min(this.paginatedResults.length - 1, 9)
      
      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault()
          if (this.selectedIndex < maxIndex) {
            this.selectedIndex++
          } else if (this.canGoToNextPage) {
            this.goToNextPage()
            this.selectedIndex = 0
          } else {
            this.selectedIndex = 0
          }
          break
        case 'ArrowUp':
          event.preventDefault()
          if (this.selectedIndex > 0) {
            this.selectedIndex--
          } else if (this.canGoToPreviousPage) {
            this.goToPreviousPage()
            this.selectedIndex = Math.min(this.paginatedResults.length - 1, 9)
          } else {
            this.selectedIndex = maxIndex
          }
          break
        case 'Tab':
          event.preventDefault()
          if (event.shiftKey) {
            if (this.selectedIndex > 0) {
              this.selectedIndex--
            } else if (this.canGoToPreviousPage) {
              this.goToPreviousPage()
              this.selectedIndex = Math.min(this.paginatedResults.length - 1, 9)
            } else {
              this.selectedIndex = maxIndex
            }
          } else {
            if (this.selectedIndex < maxIndex) {
              this.selectedIndex++
            } else if (this.canGoToNextPage) {
              this.goToNextPage()
              this.selectedIndex = 0
            } else {
              this.selectedIndex = 0
            }
          }
          break
        case 'Enter':
          event.preventDefault()
          
          if (this.searchQuery.trim().startsWith('/')) {
            const command = this.searchQuery.trim()
            
            if (command === '/debug') {
              this.toggleDebugPanel()
            }
            
            this.clearSearch()
            return
          }
          
          if (this.selectedIndex >= 0 && this.selectedIndex <= maxIndex) {
            this.selectSpell(this.paginatedResults[this.selectedIndex])
          }
          break
        case 'ArrowLeft':
          event.preventDefault()
          this.goToPreviousPage()
          break
        case 'ArrowRight':
          event.preventDefault()
          this.goToNextPage()
          break
        case 'Escape':
          this.showDropdown = false
          this.selectedIndex = -1
          this.$refs.searchInput.blur()
          break
      }
    },
    
    handleOutsideClick(event) {
      const searchContainer = this.$el.querySelector('.global-search-container')
      if (searchContainer && !searchContainer.contains(event.target)) {
        this.showDropdown = false
      }
    },
    
    highlightMatch(text) {
      if (!this.searchQuery) return text
      const regex = new RegExp(`(${this.searchQuery})`, 'gi')
      return text.replace(regex, '<mark>$1</mark>')
    },
    
    handleIconError(event) {
      event.target.style.display = 'none'
    },
    
    goToPreviousPage() {
      if (this.canGoToPreviousPage) {
        this.currentPage--
        this.selectedIndex = -1
      }
    },
    
    goToNextPage() {
      if (this.canGoToNextPage) {
        this.currentPage++
        this.selectedIndex = -1
      }
    },
    

    toggleDebugPanel() {
      this.$emit('toggle-debug-panel')
    }
  }
}
</script>

<style scoped>
.hero-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  text-align: center;
  margin-bottom: 80px;
  position: relative;
  background: transparent;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: -60%;
  left: 50%;
  transform: translateX(-50%);
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(var(--primary-rgb), 0.2) 0%, rgba(106, 76, 147, 0.15) 30%, transparent 70%);
  border-radius: 50%;
  filter: blur(100px);
  z-index: -1;
}

.main-title {
  font-family: 'Cinzel', serif;
  font-size: 5.5em;
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary-color) 0%, #c8a8ff 50%, rgba(255,255,255,0.9) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 30px;
  text-shadow: 0 0 40px rgba(var(--primary-rgb), 0.6);
  animation: glow 4s ease-in-out infinite alternate;
  letter-spacing: 2px;
}

@keyframes glow {
  from { 
    text-shadow: 0 0 30px rgba(var(--primary-rgb), 0.5);
    transform: scale(1);
  }
  to { 
    text-shadow: 0 0 50px rgba(var(--primary-rgb), 0.8), 0 0 80px rgba(147, 112, 219, 0.4);
    transform: scale(1.01);
  }
}

.main-subtitle {
  font-size: 1.8em;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 400;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 40px;
  position: relative;
}

.main-subtitle::after {
  content: '';
  position: absolute;
  bottom: -15px;
  left: 50%;
  transform: translateX(-50%);
  width: 120px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--primary-color), transparent);
}

.navigation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 35px;
  margin-top: 60px;
  padding: 0 20px;
}

.nav-card {
  background: linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(255,255,255,0.15);
  border-radius: 24px;
  padding: 40px 30px;
  text-align: left;
  position: relative;
  overflow: hidden;
  transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  cursor: pointer;
  text-decoration: none;
  color: inherit;
  display: flex;
  align-items: center;
  gap: 30px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  min-height: 140px;
}

.nav-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
  transition: left 0.8s;
}

.nav-card:hover::before {
  left: 100%;
}

.nav-card:hover {
  transform: translateY(-8px) scale(1.02);
  border-color: rgba(147, 112, 219, 0.6);
  box-shadow: 
    0 25px 60px rgba(147, 112, 219, 0.3),
    0 0 40px rgba(147, 112, 219, 0.2);
  background: linear-gradient(145deg, rgba(255,255,255,0.18), rgba(255,255,255,0.08));
}

.nav-card.placeholder {
  cursor: not-allowed;
  opacity: 0.7;
}

.nav-card.placeholder:hover {
  transform: none;
  border-color: rgba(255,255,255,0.15);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  background: linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06));
}

.nav-icon {
  width: 80px;
  height: 80px;
  border-radius: 16px;
  background: linear-gradient(135deg, #9370db, rgba(147, 112, 219, 0.8));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5em;
  color: white;
  text-shadow: 2px 2px 6px rgba(0,0,0,0.6);
  border: 3px solid rgba(255,255,255,0.4);
  box-shadow: 0 8px 24px rgba(147, 112, 219, 0.4);
  flex-shrink: 0;
  transition: all 0.4s ease;
}

.nav-card:hover .nav-icon {
  transform: scale(1.1);
  box-shadow: 0 12px 32px rgba(147, 112, 219, 0.6);
}

.nav-content {
  flex: 1;
}

.nav-title {
  font-family: 'Cinzel', serif;
  font-size: 2em;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 15px 0;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.nav-description {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.1em;
  line-height: 1.5;
  margin: 0;
}

.coming-soon-badge {
  position: absolute;
  top: 15px;
  right: 15px;
  background: linear-gradient(135deg, #ff6b6b, #ee5a24);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 0.8em;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(238, 90, 36, 0.3);
}

.nav-card.raid-nav .coming-soon-badge {
  top: 15px;
  right: 15px;
}

.nav-card.raid-nav {
  min-width: 400px;
}

/* Global Search Styles */
.global-search-container {
  position: relative;
  margin-bottom: 4rem;
  z-index: 100;
}

.search-input-wrapper {
  position: relative;
  max-width: 600px;
  margin: 0 auto;
}

.global-search-input {
  width: 100%;
  padding: 1.25rem 3.5rem 1.25rem 4rem;
  border: 2px solid rgba(147, 112, 219, 0.3);
  border-radius: 30px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.06));
  backdrop-filter: blur(20px);
  color: white;
  font-size: 1.2rem;
  font-weight: 500;
  outline: none;
  transition: all 0.3s ease;
  font-family: 'Inter', sans-serif;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.global-search-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.global-search-input:focus {
  border-color: #9370db;
  box-shadow: 0 0 25px rgba(147, 112, 219, 0.4), 0 8px 32px rgba(0, 0, 0, 0.3);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.08));
}

.search-icon {
  position: absolute;
  left: 1.5rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.3rem;
  color: rgba(255, 255, 255, 0.7);
  pointer-events: none;
}

.clear-search-btn {
  position: absolute;
  right: 1.25rem;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(147, 112, 219, 0.2);
  color: white;
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1.3rem;
  font-weight: bold;
  transition: all 0.3s ease;
}

.clear-search-btn:hover {
  background: rgba(147, 112, 219, 0.4);
  transform: translateY(-50%) scale(1.1);
}

.search-dropdown {
  position: absolute;
  top: calc(100% + 0.125rem);
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 600px;
  background: linear-gradient(145deg, rgba(20, 25, 40, 0.95), rgba(15, 20, 35, 0.98));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(147, 112, 219, 0.3);
  border-radius: 20px;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4), 0 0 60px rgba(147, 112, 219, 0.2);
  overflow: hidden;
  animation: searchDropdownFadeIn 0.3s ease-out;
  z-index: 1100;
  display: flex;
  flex-direction: column;
}

.search-dropdown.has-pagination {
  height: 520px;
}

.search-dropdown.no-pagination {
  min-height: 108px;
}

@keyframes searchDropdownFadeIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-15px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.search-results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1.5rem;
  background: rgba(147, 112, 219, 0.15);
  border-bottom: 1px solid rgba(147, 112, 219, 0.2);
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  flex-shrink: 0;
  height: 48px;
}

.page-indicator {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 400;
  text-transform: none;
  letter-spacing: normal;
}

.search-results-list {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.search-dropdown.no-pagination .search-results-list {
  padding-bottom: 20px;
}

.search-result-item {
  padding: 0.5rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: all 0.3s ease;
  height: 40px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.search-result-item:hover,
.search-result-item.highlighted {
  background: linear-gradient(145deg, rgba(147, 112, 219, 0.15), rgba(147, 112, 219, 0.08));
  transform: translateX(6px);
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
}

.search-result-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 2px solid rgba(147, 112, 219, 0.3);
  background: rgba(255, 255, 255, 0.1);
  object-fit: cover;
  flex-shrink: 0;
}

.search-result-text {
  flex: 1;
  min-width: 0;
}

.search-result-name {
  font-family: 'Cinzel', serif;
  font-size: 0.95rem;
  font-weight: 600;
  color: white;
  margin-bottom: 0.125rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2;
}

.search-result-name mark {
  background: #9370db;
  color: white;
  padding: 0.1em 0.3em;
  border-radius: 4px;
  font-weight: 700;
}

.search-result-details {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
  line-height: 1.2;
}

.spell-classes {
  color: #9370db;
  font-weight: 600;
}

.search-results-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1.5rem;
  background: rgba(147, 112, 219, 0.08);
  border-top: 1px solid rgba(147, 112, 219, 0.2);
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  flex-shrink: 0;
  height: 60px;
}

.pagination-info {
  font-style: italic;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.keyboard-tip {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  font-style: normal;
  font-weight: 400;
}

.pagination-controls {
  display: flex;
  gap: 0.5rem;
}

.pagination-arrow {
  background: rgba(147, 112, 219, 0.2);
  border: 1px solid rgba(147, 112, 219, 0.3);
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.9rem;
  font-weight: bold;
}

.pagination-arrow:hover:not(:disabled) {
  background: rgba(147, 112, 219, 0.4);
  border-color: rgba(147, 112, 219, 0.5);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(147, 112, 219, 0.3);
}

.pagination-arrow:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: rgba(147, 112, 219, 0.1);
  border-color: rgba(147, 112, 219, 0.15);
}

.pagination-arrow:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 4px rgba(147, 112, 219, 0.2);
}

.pagination-arrow.glow-attention {
  animation: arrowGlow 2s ease-in-out;
  background: rgba(147, 112, 219, 0.6) !important;
  border-color: rgba(147, 112, 219, 0.8) !important;
  box-shadow: 0 0 15px rgba(147, 112, 219, 0.8), 0 0 30px rgba(147, 112, 219, 0.4) !important;
}

@keyframes arrowGlow {
  0% {
    box-shadow: 0 2px 8px rgba(147, 112, 219, 0.3);
  }
  25% {
    box-shadow: 0 0 20px rgba(147, 112, 219, 1), 0 0 40px rgba(147, 112, 219, 0.6);
    transform: translateY(-1px) scale(1.1);
  }
  50% {
    box-shadow: 0 0 25px rgba(147, 112, 219, 1), 0 0 50px rgba(147, 112, 219, 0.8);
    transform: translateY(-2px) scale(1.15);
  }
  75% {
    box-shadow: 0 0 20px rgba(147, 112, 219, 1), 0 0 40px rgba(147, 112, 219, 0.6);
    transform: translateY(-1px) scale(1.1);
  }
  100% {
    box-shadow: 0 2px 8px rgba(147, 112, 219, 0.3);
    transform: translateY(0) scale(1);
  }
}

.search-empty {
  position: absolute;
  top: calc(100% + 0.125rem);
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 600px;
  background: linear-gradient(145deg, rgba(20, 25, 40, 0.95), rgba(15, 20, 35, 0.98));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(147, 112, 219, 0.3);
  border-radius: 20px;
  padding: 2rem;
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
  font-size: 1rem;
  z-index: 1100;
  animation: searchDropdownFadeIn 0.3s ease-out;
}

.search-loading {
  position: absolute;
  top: calc(100% + 0.125rem);
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: linear-gradient(145deg, rgba(20, 25, 40, 0.95), rgba(15, 20, 35, 0.98));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(147, 112, 219, 0.3);
  border-radius: 20px;
  padding: 1rem 2rem;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.95rem;
  z-index: 1100;
  animation: searchDropdownFadeIn 0.3s ease-out;
}

.search-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(147, 112, 219, 0.3);
  border-top: 2px solid #9370db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Cart Styles */
.hero-content {
  flex: 1;
}

.cart-container {
  position: relative;
}

.cart-button {
  background: linear-gradient(145deg, rgba(147, 112, 219, 0.2), rgba(147, 112, 219, 0.1));
  backdrop-filter: blur(10px);
  border: 2px solid rgba(147, 112, 219, 0.3);
  border-radius: 50%;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.cart-button:hover {
  background: linear-gradient(145deg, rgba(147, 112, 219, 0.3), rgba(147, 112, 219, 0.2));
  border-color: rgba(147, 112, 219, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(147, 112, 219, 0.2);
}

.cart-icon {
  font-size: 1.5rem;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.cart-counter {
  position: absolute;
  top: -8px;
  right: -8px;
  background: linear-gradient(145deg, #ff4757, #ff3742);
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
  border: 2px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

/* Cart Modal Styles */
.cart-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.cart-modal {
  background: linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(255,255,255,0.15);
  border-radius: 24px;
  max-width: 600px;
  width: 100%;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.3);
}

.cart-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.cart-modal-header h3 {
  font-family: 'Cinzel', serif;
  font-size: 1.8rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.modal-close-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 2rem;
  cursor: pointer;
  transition: color 0.3s ease;
  padding: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close-btn:hover {
  color: rgba(255, 255, 255, 1);
}

.cart-modal-content {
  padding: 1.5rem;
  max-height: 60vh;
  overflow-y: auto;
}

.cart-empty {
  text-align: center;
  padding: 2rem;
}

.cart-empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.6;
}

.cart-empty h4 {
  font-size: 1.5rem;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 1rem 0;
}

.cart-empty p {
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 2rem 0;
}

.cart-items {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.cart-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.cart-item-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.cart-item-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  object-fit: cover;
}

.cart-item-details h4 {
  margin: 0 0 0.25rem 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.1rem;
}

.cart-item-meta {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
}

.cart-item-pricing {
  display: flex;
  align-items: center;
  margin-right: 1rem;
}

.cart-coin-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.cart-coin-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: rgba(0, 0, 0, 0.3);
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.cart-coin-icon {
  width: 22px;
  height: 22px;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
}

.cart-coin-value {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.cart-pricing-free {
  color: rgba(255, 255, 255, 0.6);
  font-style: italic;
}

.remove-item-btn {
  background: linear-gradient(135deg, #dc3545, #c82333);
  border: none;
  border-radius: 8px;
  width: 40px;
  height: 40px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
}

.remove-item-btn:hover {
  background: linear-gradient(135deg, #c82333, #a71e2a);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.4);
}

.cart-total {
  padding: 1.5rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 1.5rem;
}

.cart-total-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cart-total-header h4 {
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.3rem;
}

.cart-total-coins {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.cart-total-free {
  color: rgba(255, 255, 255, 0.6);
  font-style: italic;
  font-size: 1.1rem;
}

.cart-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.clear-cart-btn {
  background: linear-gradient(135deg, #6c757d, #5a6268);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(108, 117, 125, 0.3);
}

.clear-cart-btn:hover {
  background: linear-gradient(135deg, #5a6268, #495057);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(108, 117, 125, 0.4);
}

.continue-shopping-btn {
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
}

.continue-shopping-btn:hover {
  background: linear-gradient(135deg, #0056b3, #004085);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
}

@media (max-width: 1200px) {
  .navigation-grid { grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
}

@media (max-width: 768px) {
  .main-title { font-size: 4em; }
  .main-subtitle { font-size: 1.4em; letter-spacing: 2px; }
  .navigation-grid { 
    grid-template-columns: 1fr; 
    gap: 25px; 
    padding: 0 10px;
  }
  .nav-card { 
    padding: 30px 20px; 
    flex-direction: column;
    text-align: center;
    gap: 20px;
  }
  .nav-icon { 
    width: 70px; 
    height: 70px; 
    font-size: 2em;
  }
  .nav-title { font-size: 1.8em; }
  .nav-description { font-size: 1em; }
  
  .hero-section {
    flex-direction: column;
    gap: 1rem;
  }
  
  .cart-button {
    width: 50px;
    height: 50px;
  }
  
  .cart-icon {
    font-size: 1.25rem;
  }
  
  .cart-counter {
    width: 20px;
    height: 20px;
    font-size: 0.7rem;
  }
}

@media (max-width: 480px) {
  .main-container { padding: 40px 15px; }
  .main-title { font-size: 3.2em; }
  .navigation-grid { grid-template-columns: 1fr; }
  .nav-card { padding: 25px 15px; }
  .nav-icon { width: 60px; height: 60px; font-size: 1.8em; }
  .nav-title { font-size: 1.6em; }
  .nav-description { font-size: 0.95em; }
}
</style>