<template>
  <div class="main-container">
    <div class="hero-section">
      <div class="hero-content">
        <h1 class="main-title">Clumsy's World</h1>
        <p class="main-subtitle">Class Information</p>
      </div>
      
      <!-- Cart Button -->
      <div class="cart-container">
        <button @click="openCart" class="cart-button" title="View Cart">
          <span class="cart-icon">🛒</span>
          <span v-if="cartStore.itemCount > 0" class="cart-counter">{{ cartStore.itemCount }}</span>
        </button>
      </div>
    </div>
    
    <!-- Global Spell Search -->
    <div class="global-search-container">
      <div class="search-input-wrapper">
        <input
          ref="searchInput"
          v-model="searchQuery"
          @input="handleSearchInput"
          @focus="showDropdown = true"
          @keydown="handleKeyDown"
          type="text"
          placeholder="Search spells across all classes..."
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
          No spells found matching "{{ searchQuery }}"
        </div>
        
        <!-- Loading State -->
        <div v-if="searchLoading" class="search-loading">
          <div class="search-spinner"></div>
          <span>Searching...</span>
        </div>
      </div>
      
      <!-- Refresh Data Message -->
      <div v-if="hasUncachedClasses" class="refresh-message">
        <div class="refresh-content">
          <span class="refresh-icon">⚠️</span>
          <span class="refresh-text">
            {{ uncachedClasses.length }} class{{ uncachedClasses.length === 1 ? '' : 'es' }} need spell data for search functionality.
          </span>
          <button @click="refreshAllSpellData" class="refresh-button" :disabled="isRefreshing">
            <span v-if="isRefreshing" class="refresh-spinner"></span>
            {{ isRefreshing ? 'Loading...' : 'Load All Spell Data' }}
          </button>
        </div>
      </div>
    </div>
    
    <div class="classes-grid">
      <router-link 
        v-for="cls in classes" 
        :key="cls.name"
        :to="isClassHydrated(cls.name) ? { name: 'ClassSpells', params: { className: cls.name.toLowerCase() } } : ''"
        :class="[
          'class-card', 
          cls.name.toLowerCase(),
          {
            'hydrated': isClassHydrated(cls.name),
            'not-hydrated': !isClassHydrated(cls.name),
            'cached': getCacheStatusForClass(cls.name).cached,
            'uncached': !getCacheStatusForClass(cls.name).cached
          }
        ]"
        @click="handleClassClick(cls.name, $event)"
      >
        <div class="class-icon">
          <img 
            :src="`/icons/${cls.name.toLowerCase()}.gif`" 
            :alt="cls.name"
            @error="handleImageError"
          >
        </div>
        <div class="class-name">{{ cls.name }}</div>
        <div v-if="!isClassHydrated(cls.name)" class="loading-indicator">
          <div class="loading-spinner"></div>
        </div>
        <div v-if="!isClassHydrated(cls.name)" class="loading-label">Loading</div>
      </router-link>
    </div>
    
    <!-- Cart Modal -->
    <div v-if="cartStore.isOpen" class="cart-modal-overlay" @click="cartStore.closeCart()">
      <div class="cart-modal" @click.stop>
        <div class="cart-modal-header">
          <h3>Shopping Cart</h3>
          <button @click="cartStore.closeCart()" class="modal-close-btn">×</button>
        </div>
        
        <div class="cart-modal-content">
          <!-- Empty Cart State -->
          <div v-if="cartStore.itemCount === 0" class="cart-empty">
            <div class="cart-empty-icon">🛒</div>
            <h4>Your cart is empty</h4>
            <p>Browse spells and add them to your cart to see them here.</p>
            <button @click="cartStore.closeCart()" class="continue-shopping-btn">
              Continue Shopping
            </button>
          </div>
          
          <!-- Cart Items -->
          <div v-else>
            <div class="cart-items">
              <div 
                v-for="item in cartStore.items" 
                :key="item.spell_id"
                class="cart-item"
              >
                <div class="cart-item-info">
                  <img 
                    v-if="item.icon" 
                    :src="item.icon" 
                    :alt="item.name"
                    class="cart-item-icon"
                    @error="handleIconError"
                  />
                  <div class="cart-item-details">
                    <h4 class="cart-item-name">{{ item.name }}</h4>
                    <div class="cart-item-meta">
                      Level {{ item.level }}
                      <span v-if="item.class_names && item.class_names.length">
                        • {{ item.class_names.join(', ') }}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div class="cart-item-pricing">
                  <div v-if="item.pricing && hasAnyPrice(item.pricing)" class="cart-coin-display">
                    <div v-if="item.pricing.platinum > 0" class="cart-coin-item">
                      <img src="/icons/coins/platinum.svg" alt="Platinum" class="cart-coin-icon" />
                      <span class="cart-coin-value">{{ item.pricing.platinum }}</span>
                    </div>
                    <div v-if="item.pricing.gold > 0" class="cart-coin-item">
                      <img src="/icons/coins/gold.svg" alt="Gold" class="cart-coin-icon" />
                      <span class="cart-coin-value">{{ item.pricing.gold }}</span>
                    </div>
                    <div v-if="item.pricing.silver > 0" class="cart-coin-item">
                      <img src="/icons/coins/silver.svg" alt="Silver" class="cart-coin-icon" />
                      <span class="cart-coin-value">{{ item.pricing.silver }}</span>
                    </div>
                    <div v-if="item.pricing.bronze > 0" class="cart-coin-item">
                      <img src="/icons/coins/bronze.svg" alt="Bronze" class="cart-coin-icon" />
                      <span class="cart-coin-value">{{ item.pricing.bronze }}</span>
                    </div>
                  </div>
                  <div v-else class="cart-pricing-free">Free</div>
                </div>
                
                <button 
                  @click="removeFromCart(item.spell_id)" 
                  class="remove-item-btn"
                  title="Remove from cart"
                >
                  🗑️
                </button>
              </div>
            </div>
            
            <!-- Cart Total -->
            <div class="cart-total">
              <div class="cart-total-header">
                <h4>Total Cost</h4>
                <div class="cart-total-coins">
                  <div v-if="cartStore.optimizedTotal.platinum > 0" class="cart-coin-item">
                    <img src="/icons/coins/platinum.svg" alt="Platinum" class="cart-coin-icon" />
                    <span class="cart-coin-value">{{ cartStore.optimizedTotal.platinum }}</span>
                  </div>
                  <div v-if="cartStore.optimizedTotal.gold > 0" class="cart-coin-item">
                    <img src="/icons/coins/gold.svg" alt="Gold" class="cart-coin-icon" />
                    <span class="cart-coin-value">{{ cartStore.optimizedTotal.gold }}</span>
                  </div>
                  <div v-if="cartStore.optimizedTotal.silver > 0" class="cart-coin-item">
                    <img src="/icons/coins/silver.svg" alt="Silver" class="cart-coin-icon" />
                    <span class="cart-coin-value">{{ cartStore.optimizedTotal.silver }}</span>
                  </div>
                  <div v-if="cartStore.optimizedTotal.bronze > 0" class="cart-coin-item">
                    <img src="/icons/coins/bronze.svg" alt="Bronze" class="cart-coin-icon" />
                    <span class="cart-coin-value">{{ cartStore.optimizedTotal.bronze }}</span>
                  </div>
                  <div v-if="cartStore.totalInBronze === 0" class="cart-total-free">No cost</div>
                </div>
              </div>
            </div>
            
            <!-- Cart Actions -->
            <div class="cart-actions">
              <button @click="clearCart()" class="clear-cart-btn">
                Clear Cart
              </button>
              <button @click="cartStore.closeCart()" class="continue-shopping-btn">
                Continue Shopping
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading Modal -->
    <div v-if="showRefreshModal" class="refresh-modal-overlay" @click="closeRefreshModal">
      <div class="refresh-modal" @click.stop>
        <div class="refresh-modal-header">
          <h3>Loading Spell Data</h3>
          <button v-if="!isRefreshing" @click="closeRefreshModal" class="modal-close-btn">×</button>
        </div>
        
        <div class="refresh-modal-content">
          <div class="progress-container">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: refreshProgress + '%' }"
                :class="{ 'complete': loadingComplete }"
              ></div>
            </div>
            <div class="progress-text">{{ refreshProgress }}%</div>
          </div>
          
          <div class="status-text">
            <span v-if="loadingComplete" class="status-complete">
              ✅ All spell data loaded successfully!
            </span>
            <span v-else class="status-loading">
              📚 Loading {{ currentlyLoading }}...
            </span>
          </div>
          
          <div class="loading-details">
            <div class="loading-animation">
              <img 
                v-if="currentlyLoading && !loadingComplete"
                :src="`/icons/${currentlyLoading.toLowerCase()}.gif`" 
                :alt="`${currentlyLoading} icon`"
                class="class-loading-icon"
                @error="handleLoadingIconError"
              />
              <div v-else class="spell-icon-bounce">✅</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useSpellsStore } from '../stores/spells'
import { useCartStore } from '../stores/cart'
import axios from 'axios'

// Configure API base URL - use environment variable in production, relative path in development
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 
  (import.meta.env.PROD ? 'https://eqdatascraper-backend-production.up.railway.app' : '')

export default {
  name: 'Home',
  data() {
    return {
      searchQuery: '',
      searchResults: [],
      showDropdown: false,
      selectedIndex: -1,
      searchLoading: false,
      searchTimeout: null,
      cacheStatus: {},
      showRefreshModal: false,
      refreshProgress: 0,
      currentlyLoading: '',
      loadingComplete: false,
      isRefreshing: false,
      currentPage: 0,
      resultsPerPage: 10,
      showRightArrowGlow: false
    }
  },
  setup() {
    const spellsStore = useSpellsStore()
    const cartStore = useCartStore()
    
    // Load cart from localStorage on component mount
    cartStore.loadFromLocalStorage()
    
    return {
      classes: spellsStore.classes,
      spellsStore,
      cartStore
    }
  },
  computed: {
    uncachedClasses() {
      return this.classes.filter(cls => !this.getCacheStatusForClass(cls.name).cached)
    },
    
    hasUncachedClasses() {
      return this.uncachedClasses.length > 0
    },
    
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
    await this.checkCacheStatus()
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleOutsideClick)
    if (this.searchTimeout) {
      clearTimeout(this.searchTimeout)
    }
  },
  methods: {
    handleImageError(event) {
      const fallbackUrl = `https://wiki.heroesjourneyemu.com/${event.target.alt.toLowerCase()}.gif`
      event.target.src = fallbackUrl
      event.target.onerror = () => {
        event.target.style.display = 'none'
      }
    },
    
    handleSearchInput() {
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
      
      this.searchLoading = true
      
      try {
        const response = await axios.get(`${API_BASE_URL}/api/search-spells?q=${encodeURIComponent(this.searchQuery)}`)
        this.searchResults = response.data.results || []
        this.showDropdown = true
        this.selectedIndex = -1
        this.currentPage = 0 // Reset to first page on new search
        
        // Trigger glow effect if there are more than 10 results
        if (this.searchResults.length > this.resultsPerPage) {
          this.$nextTick(() => {
            this.showRightArrowGlow = true
            setTimeout(() => {
              this.showRightArrowGlow = false
            }, 2000) // Glow for 2 seconds
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
      if (!this.showDropdown || this.searchResults.length === 0) return
      
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
            // Shift+Tab - cycle backwards
            if (this.selectedIndex > 0) {
              this.selectedIndex--
            } else if (this.canGoToPreviousPage) {
              this.goToPreviousPage()
              this.selectedIndex = Math.min(this.paginatedResults.length - 1, 9)
            } else {
              this.selectedIndex = maxIndex
            }
          } else {
            // Tab - cycle forwards
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
    
    handleLoadingIconError(event) {
      // Fallback to generic icon if class icon fails to load
      event.target.style.display = 'none'
      const parent = event.target.parentElement
      if (parent) {
        parent.innerHTML = '<div class="spell-icon-bounce">🔮</div>'
      }
    },
    
    async checkCacheStatus() {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/cache-status`)
        this.cacheStatus = response.data
      } catch (error) {
        console.error('Error checking cache status:', error)
        this.cacheStatus = {}
      }
    },
    
    getCacheStatusForClass(className) {
      return this.cacheStatus[className] || { cached: false, spell_count: 0 }
    },

    isClassHydrated(className) {
      // Check if a class has been hydrated (loaded into memory) using the store getter
      return this.spellsStore.isClassHydrated(className)
    },

    handleClassClick(className, event) {
      // Prevent navigation if class is not hydrated
      if (!this.isClassHydrated(className)) {
        event.preventDefault()
        console.log(`Class ${className} not yet hydrated - navigation prevented`)
        return false
      }
      // Allow normal navigation for hydrated classes
      return true
    },
    
    
    async refreshAllSpellData() {
      this.showRefreshModal = true
      this.isRefreshing = true
      this.refreshProgress = 0
      this.loadingComplete = false
      
      const classesToLoad = this.uncachedClasses
      const totalClasses = classesToLoad.length
      
      for (let i = 0; i < classesToLoad.length; i++) {
        const cls = classesToLoad[i]
        this.currentlyLoading = cls.name
        
        try {
          console.log(`Loading spells for ${cls.name}...`)
          const response = await axios.get(`${API_BASE_URL}/api/spells/${cls.name.toLowerCase()}`)
          
          // Check if we got HTML instead of JSON (proxy routing issue)
          if (typeof response.data === 'string' && response.data.includes('<!DOCTYPE html>')) {
            throw new Error(`API returned HTML instead of JSON for ${cls.name} - possible proxy routing issue`)
          }
          
          console.log(`Successfully loaded ${response.data.spell_count} spells for ${cls.name}`)
          
          // Update cache status for this class
          this.cacheStatus[cls.name] = { 
            cached: true, 
            spell_count: response.data.spell_count || 0,
            last_updated: response.data.last_updated || new Date().toISOString()
          }
          
          this.refreshProgress = Math.round(((i + 1) / totalClasses) * 100)
          
          // Small delay to show progress
          await new Promise(resolve => setTimeout(resolve, 500))
          
        } catch (error) {
          console.error(`Error loading ${cls.name}:`, error)
          console.error('Error details:', error.response?.data || error.message)
          console.error('Response type:', typeof error.response?.data)
          
          // Still update progress even on error
          this.refreshProgress = Math.round(((i + 1) / totalClasses) * 100)
        }
      }
      
      this.loadingComplete = true
      this.currentlyLoading = 'Complete!'
      
      // Refresh cache status to update the UI
      await this.checkCacheStatus()
      
      // Keep modal open for a moment to show completion
      setTimeout(() => {
        this.showRefreshModal = false
        this.isRefreshing = false
        this.refreshProgress = 0
      }, 1500)
    },
    
    closeRefreshModal() {
      if (!this.isRefreshing) {
        this.showRefreshModal = false
      }
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
    
    openCart() {
      this.cartStore.openCart()
    },

    removeFromCart(spellId) {
      this.cartStore.removeItem(spellId)
    },

    clearCart() {
      if (confirm('Are you sure you want to clear your cart?')) {
        this.cartStore.clearCart()
      }
    },

    hasAnyPrice(pricing) {
      if (!pricing) return false
      return pricing.platinum > 0 || pricing.gold > 0 || pricing.silver > 0 || pricing.bronze > 0
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

.classes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 35px;
  margin-top: 60px;
  padding: 0 20px;
}

.class-card {
  background: linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(255,255,255,0.15);
  border-radius: 24px;
  padding: 50px 20px;
  text-align: center;
  position: relative;
  overflow: hidden;
  transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  cursor: pointer;
  text-decoration: none;
  color: inherit;
  height: 384px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.class-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
  transition: left 0.8s;
}

.class-card::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(var(--class-color), 0.05), transparent);
  opacity: 0;
  transition: opacity 0.5s ease;
  pointer-events: none;
}

.class-card:hover::before {
  left: 100%;
}

.class-card:hover::after {
  opacity: 1;
}

.class-card:hover {
  transform: translateY(-15px) scale(1.03);
  border-color: rgba(var(--class-color-rgb), 0.6);
  box-shadow: 
    0 25px 60px rgba(var(--class-color-rgb), 0.3),
    0 0 40px rgba(var(--class-color-rgb), 0.2);
  background: linear-gradient(145deg, rgba(255,255,255,0.18), rgba(255,255,255,0.08));
}

.class-icon {
  width: 120px;
  height: 120px;
  margin-bottom: 35px;
  border-radius: 16px;
  transition: all 0.4s ease;
  animation: float 4s ease-in-out infinite;
  background: linear-gradient(135deg, var(--class-color), rgba(255,255,255,0.2));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.2em;
  font-weight: bold;
  color: white;
  text-shadow: 2px 2px 6px rgba(0,0,0,0.6);
  border: 3px solid rgba(255,255,255,0.4);
  box-shadow: 0 8px 24px rgba(var(--class-color-rgb), 0.4);
  position: relative;
  overflow: hidden;
}

.class-icon::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
  transform: rotate(45deg);
  transition: transform 0.6s ease;
}

.class-card:hover .class-icon::before {
  transform: rotate(45deg) translate(50%, 50%);
}

.class-icon img {
  width: 85%;
  height: 85%;
  object-fit: cover;
  border-radius: 12px;
  z-index: 1;
  position: relative;
}

.class-icon.fallback {
  font-family: 'Cinzel', serif;
}

@keyframes float {
  0%, 100% { transform: translateY(0px) rotateY(0deg); }
  25% { transform: translateY(-8px) rotateY(2deg); }
  50% { transform: translateY(-5px) rotateY(0deg); }
  75% { transform: translateY(-12px) rotateY(-2deg); }
}

.class-card:hover .class-icon {
  transform: scale(1.15) translateY(-8px);
  animation-play-state: paused;
  box-shadow: 0 15px 40px rgba(var(--class-color-rgb), 0.6);
}

.class-name {
  font-family: 'Cinzel', serif;
  font-size: 1.9em;
  font-weight: 600;
  color: var(--text-dark);
  transition: all 0.4s ease;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
  letter-spacing: 1px;
}

.class-card:hover .class-name {
  color: var(--class-color);
  text-shadow: 
    0 0 15px rgba(var(--class-color-rgb), 0.6),
    0 2px 4px rgba(0,0,0,0.5);
  transform: translateY(-2px);
}

@media (max-width: 1200px) {
  .classes-grid { grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
}

@media (max-width: 768px) {
  .main-title { font-size: 4em; }
  .main-subtitle { font-size: 1.4em; letter-spacing: 2px; }
  .classes-grid { 
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); 
    gap: 25px; 
    padding: 0 10px;
  }
  .class-card { height: 336px; padding: 40px 15px; }
  .class-icon { width: 100px; height: 100px; margin-bottom: 30px; }
  .class-name { font-size: 1.6em; }
}

@media (max-width: 480px) {
  .main-container { padding: 40px 15px; }
  .main-title { font-size: 3.2em; }
  .classes-grid { grid-template-columns: 1fr; }
  .class-card { height: 312px; padding: 35px 15px; }
  .class-icon { width: 90px; height: 90px; margin-bottom: 25px; }
}

/* Global Search Styles */
.global-search-container {
  position: relative;
  margin-bottom: 4rem;
  z-index: 100;
}

.global-search-container:has(.refresh-message) {
  margin-bottom: 3rem;
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

/* Full height when 10 results (with pagination) */
.search-dropdown.has-pagination {
  height: 520px; /* Fixed height: header(48px) + 10*results(40px each) + footer(60px) + padding(12px) */
}

/* Dynamic height when fewer than 10 results (no pagination) */
.search-dropdown.no-pagination {
  min-height: 108px; /* header(48px) + 1*result(40px) + padding(20px) */
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
  overflow: hidden; /* No scrolling */
  display: flex;
  flex-direction: column;
}

/* Add bottom padding when no pagination */
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

@media (max-width: 768px) {
  .global-search-container {
    margin-bottom: 3rem;
  }
  
  .global-search-input {
    font-size: 1.1rem;
    padding: 1rem 3rem 1rem 3.5rem;
  }
  
  .search-dropdown {
    margin: 0 1rem;
    width: calc(100% - 2rem);
  }
}

/* Hydration Status Borders - Primary States */
.class-card.hydrated {
  border-color: #22c55e !important; /* Green for hydrated (ready for instant loading) */
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2), 0 0 0 1px #22c55e;
  cursor: pointer;
}

.class-card.not-hydrated {
  border-color: #6b7280 !important; /* Gray for not hydrated (disabled) */
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1), 0 0 0 1px #6b7280;
  opacity: 0.6;
  cursor: not-allowed;
  position: relative;
}

/* Cache Status Borders - Secondary Indicators */
.class-card.cached {
  /* Hydrated classes will override this with green */
}

.class-card.uncached {
  /* Not-hydrated classes will override this with gray */
}

/* Hover States for Hydrated/Not-Hydrated */
.class-card.hydrated:hover {
  border-color: #16a34a !important;
  box-shadow: 0 25px 60px rgba(34, 197, 94, 0.3), 0 0 40px rgba(34, 197, 94, 0.2);
  transform: translateY(-8px);
  transition: all 0.3s ease;
}

.class-card.not-hydrated:hover {
  /* No hover effect for disabled cards */
  transform: none;
}

/* Loading Indicator for Non-Hydrated Classes */
.loading-indicator {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s linear infinite;
}

/* Stylized Loading Label */
.loading-label {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(107, 114, 128, 0.9);
  color: #fff;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  z-index: 11;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.8;
  }
  50% {
    opacity: 1;
  }
}

/* Refresh Message */
.refresh-message {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.04));
  backdrop-filter: blur(15px);
  border: 1px solid rgba(147, 112, 219, 0.2);
  border-top: none;
  border-radius: 0 0 16px 16px;
  padding: 0.75rem 1rem;
  margin: 0 auto;
  max-width: 540px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  opacity: 0.95;
  position: relative;
  z-index: 50;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 0.95;
    transform: translateY(0);
  }
}

.refresh-content {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  justify-content: space-between;
  flex-wrap: wrap;
}

.refresh-icon {
  font-size: 1rem;
  flex-shrink: 0;
  opacity: 0.8;
}

.refresh-text {
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.8rem;
  font-weight: 400;
  flex: 1;
  min-width: 180px;
}

.refresh-button {
  background: linear-gradient(135deg, rgba(147, 112, 219, 0.8), rgba(147, 112, 219, 0.6));
  color: white;
  border: 1px solid rgba(147, 112, 219, 0.4);
  border-radius: 8px;
  padding: 0.4rem 0.8rem;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  min-width: 120px;
  justify-content: center;
  white-space: nowrap;
}

.refresh-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #9370db, rgba(147, 112, 219, 0.9));
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(147, 112, 219, 0.3);
  border-color: rgba(147, 112, 219, 0.6);
}

.refresh-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.refresh-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Loading Modal */
.refresh-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  animation: modalFadeIn 0.3s ease-out;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.refresh-modal {
  background: linear-gradient(145deg, rgba(30, 35, 50, 0.95), rgba(20, 25, 40, 0.98));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(147, 112, 219, 0.3);
  border-radius: 24px;
  padding: 0;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.5), 0 0 80px rgba(147, 112, 219, 0.3);
  animation: modalSlideIn 0.3s ease-out;
  overflow: hidden;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.refresh-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2rem 2rem 1rem;
  border-bottom: 1px solid rgba(147, 112, 219, 0.2);
}

.refresh-modal-header h3 {
  font-family: 'Cinzel', serif;
  font-size: 1.5rem;
  font-weight: 600;
  color: white;
  margin: 0;
  text-shadow: 0 0 20px rgba(147, 112, 219, 0.4);
}

.modal-close-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.modal-close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.refresh-modal-content {
  padding: 2rem;
}

.progress-container {
  position: relative;
  margin-bottom: 2rem;
}

.progress-bar {
  width: 100%;
  height: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid rgba(147, 112, 219, 0.3);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #9370db, #c8a8ff);
  border-radius: 6px;
  transition: width 0.5s ease;
  position: relative;
  overflow: hidden;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: progressShimmer 2s infinite;
}

.progress-fill.complete {
  background: linear-gradient(90deg, #22c55e, #16a34a);
}

@keyframes progressShimmer {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
}

.progress-text {
  position: absolute;
  top: 50%;
  right: 8px;
  transform: translateY(-50%);
  color: white;
  font-size: 0.8rem;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
}

.status-text {
  text-align: center;
  margin-bottom: 1.5rem;
  min-height: 24px;
}

.status-loading {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1rem;
  font-weight: 500;
}

.status-complete {
  color: #22c55e;
  font-size: 1rem;
  font-weight: 600;
}

.loading-details {
  display: flex;
  justify-content: center;
  align-items: center;
}

.loading-animation {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.spell-icon-bounce {
  font-size: 2rem;
  animation: bounce 1.5s ease-in-out infinite;
}

.class-loading-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  border: 2px solid rgba(147, 112, 219, 0.4);
  background: rgba(255, 255, 255, 0.1);
  object-fit: cover;
  animation: bounce 1.5s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  25% {
    transform: translateY(-8px) rotate(5deg);
  }
  50% {
    transform: translateY(-4px) rotate(0deg);
  }
  75% {
    transform: translateY(-12px) rotate(-5deg);
  }
}

@media (max-width: 768px) {
  .global-search-container {
    margin-bottom: 3rem;
  }
  
  .global-search-container:has(.refresh-message) {
    margin-bottom: 2.5rem;
  }
  
  .refresh-message {
    max-width: calc(100% - 2rem);
    margin: 0 1rem;
  }
  
  .refresh-content {
    flex-direction: column;
    text-align: center;
    gap: 0.5rem;
  }
  
  .refresh-text {
    min-width: auto;
    font-size: 0.75rem;
  }
  
  .refresh-button {
    min-width: 100px;
    font-size: 0.7rem;
    padding: 0.35rem 0.7rem;
  }
  
  .refresh-modal {
    width: 95%;
    margin: 1rem;
  }
  
  .refresh-modal-header,
  .refresh-modal-content {
    padding: 1.5rem;
  }
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

@media (max-width: 768px) {
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
  
  .cart-modal {
    margin: 0.5rem;
    max-height: 90vh;
  }
  
  .cart-modal-header {
    padding: 1rem;
  }
  
  .cart-modal-content {
    padding: 1rem;
  }
  
  .cart-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .cart-item-info {
    width: 100%;
  }
  
  .cart-item-pricing {
    margin-right: 0;
    align-self: flex-end;
  }
  
  .cart-total-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .cart-actions {
    flex-direction: column;
  }
  
  .cart-coin-display {
    gap: 0.375rem;
  }
  
  .cart-total-coins {
    gap: 0.5rem;
  }
}
</style> 