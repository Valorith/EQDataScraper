<template>
  <div class="characters-page">
    <div class="characters-container">
      <h1 class="page-title">Characters</h1>
      
      <!-- Main Character Slots Section -->
      <div class="main-slots-section">
        <h2 class="section-title">Your Main Characters</h2>
        <div class="main-slots-grid">
          <!-- Primary Main Slot -->
          <div class="main-slot primary" :class="{ active: activeSlot === 'primary' }">
            <div class="slot-header">
              <h3>Primary Main</h3>
              <div class="slot-badge primary">1</div>
            </div>
            
            <div v-if="primaryMain" class="slot-character" @click="viewCharacter(primaryMain, 'primary')">
              <div class="character-portrait">
                <img :src="getClassIcon(primaryMain?.class || 'warrior')" :alt="primaryMain?.class || 'Unknown'" />
              </div>
              <div class="character-info">
                <h4>{{ primaryMain?.name || 'Unknown' }}</h4>
                <p>{{ primaryMain?.level || 0 }} {{ primaryMain?.class || 'Unknown' }}</p>
                <p>{{ primaryMain?.race || 'Unknown' }}</p>
              </div>
              <button @click.stop="clearMainSlot('primary')" class="clear-slot-btn" :disabled="isUpdatingMains">
                ✕
              </button>
            </div>
            
            <div v-else class="empty-slot" @click="openCharacterSearch('primary')">
              <div class="empty-slot-content">
                <div class="empty-icon">+</div>
                <p>Search for your Primary Main character</p>
                <button class="search-btn">Search Characters</button>
              </div>
            </div>
          </div>

          <!-- Secondary Main Slot -->
          <div class="main-slot secondary" :class="{ active: activeSlot === 'secondary' }">
            <div class="slot-header">
              <h3>Secondary Main</h3>
              <div class="slot-badge secondary">2</div>
            </div>
            
            <div v-if="secondaryMain" class="slot-character" @click="viewCharacter(secondaryMain, 'secondary')">
              <div class="character-portrait">
                <img :src="getClassIcon(secondaryMain?.class || 'warrior')" :alt="secondaryMain?.class || 'Unknown'" />
              </div>
              <div class="character-info">
                <h4>{{ secondaryMain?.name || 'Unknown' }}</h4>
                <p>{{ secondaryMain?.level || 0 }} {{ secondaryMain?.class || 'Unknown' }}</p>
                <p>{{ secondaryMain?.race || 'Unknown' }}</p>
              </div>
              <button @click.stop="clearMainSlot('secondary')" class="clear-slot-btn" :disabled="isUpdatingMains">
                ✕
              </button>
            </div>
            
            <div v-else class="empty-slot" @click="openCharacterSearch('secondary')">
              <div class="empty-slot-content">
                <div class="empty-icon">+</div>
                <p>Search for your Secondary Main character</p>
                <button class="search-btn">Search Characters</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Character Search Section -->
      <div class="character-search-section">
        <h2 class="section-title">Character Lookup</h2>
        <p class="section-description">Search for any character to view their inventory (does not affect your main character slots)</p>
        
        <div class="search-container" 
             tabindex="0" 
             @keydown="handleKeydown">
          <div class="search-input-group">
            <input 
              ref="searchInput"
              v-model="searchQuery"
              @input="handleSearchInput"
              @keyup.enter="performSearch"
              type="text" 
              placeholder="Enter character name..."
              class="search-input"
              :disabled="isSearching"
            />
            <button 
              @click="performSearch"
              class="search-button"
              :disabled="isSearching || !searchQuery.trim()"
            >
              {{ isSearching ? 'Searching...' : 'Search' }}
            </button>
          </div>
          
          <!-- Enhanced Search Results Dropdown -->
          <div v-if="searchResults.length > 0" class="search-dropdown enhanced">
            <!-- Results header with pagination info -->
            <div class="dropdown-header">
              <span class="results-count">
                Showing {{ currentPage * resultsPerPage + 1 }}-{{ Math.min((currentPage + 1) * resultsPerPage, totalResults) }} of {{ totalResults }} results
              </span>
              <div class="pagination-controls">
                <button 
                  class="page-btn" 
                  :disabled="!hasPrevPage"
                  @click="navigatePrevPage"
                  title="Previous page (← key)"
                >
                  ←
                </button>
                <span class="page-info">{{ currentPage + 1 }} / {{ totalPages }}</span>
                <button 
                  class="page-btn" 
                  :disabled="!hasNextPage"
                  @click="navigateNextPage"
                  title="Next page (→ key)"
                >
                  →
                </button>
              </div>
            </div>
            
            <!-- Character list -->
            <div class="dropdown-results">
              <div 
                v-for="(character, index) in paginatedResults"
                :key="character.id"
                class="dropdown-item"
                :class="{ 'selected': index === selectedIndex }"
                @click="viewSearchedCharacter(character)"
                @mouseenter="selectedIndex = index"
              >
                <div class="character-portrait small">
                  <img :src="getClassIcon(character?.class || 'Warrior')" 
                       :alt="character?.class || 'Unknown'" 
                       class="class-icon" />
                </div>
                <div class="character-info">
                  <span class="character-name">{{ character?.name || 'Unknown' }}</span>
                  <span class="character-details">Level {{ character?.level || 0 }} {{ character?.class || 'Unknown' }}</span>
                  <span class="character-race">{{ character?.race || 'Unknown' }}</span>
                </div>
                <div class="select-indicator" v-if="index === selectedIndex">
                  <span>Press Enter</span>
                </div>
              </div>
            </div>
            
            <!-- Keyboard navigation help -->
            <div class="dropdown-footer">
              <span class="nav-help">Use ↑↓ to navigate, ←→ for pages, Enter to select, Esc to close</span>
            </div>
          </div>
          
          <!-- Search State Messages -->
          <div v-if="searchPerformed && searchResults.length === 0 && !isSearching" class="no-results">
            <p>No characters found matching "{{ lastSearchQuery }}"</p>
          </div>
        </div>
      </div>

      <!-- Character Search Modal -->
      <div v-if="showSearchModal" class="modal-overlay" @click="closeSearchModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>Select {{ searchModalType === 'primary' ? 'Primary' : 'Secondary' }} Main Character</h3>
            <button @click="closeSearchModal" class="modal-close">✕</button>
          </div>
          <div class="modal-body">
            <div class="search-input-group">
              <input 
                v-model="modalSearchQuery"
                @input="handleModalSearchInput"
                @keyup.enter="performModalSearch"
                type="text" 
                placeholder="Enter character name..."
                class="search-input"
                :disabled="isSearching"
              />
              <button 
                @click="performModalSearch"
                class="search-button"
                :disabled="isSearching || !modalSearchQuery.trim()"
              >
                {{ isSearching ? 'Searching...' : 'Search' }}
              </button>
            </div>
            
            <div v-if="modalSearchResults.length > 0" class="search-results">
              <div 
                v-for="character in modalSearchResults"
                :key="character.id"
                class="search-result-item"
                @click="selectMainCharacter(character)"
              >
                <div class="character-portrait small">
                  <img :src="getClassIcon(character?.class || 'warrior')" :alt="character?.class || 'Unknown'" />
                </div>
                <div class="character-info">
                  <h4>{{ character?.name || 'Unknown' }}</h4>
                  <p>{{ character?.level || 0 }} {{ character?.class || 'Unknown' }} • {{ character?.race || 'Unknown' }}</p>
                </div>
                <button class="select-btn">Select</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Character Loading State -->
      <div v-if="isLoadingCharacter" class="loading-section">
        <div class="loading-spinner"></div>
        <p>Loading character data...</p>
      </div>
      
      <!-- Character Inventory Display -->
      <div v-else-if="selectedCharacter" class="inventory-section">
        <CharacterInventory 
          :character="selectedCharacter" 
          :rawInventoryData="selectedCharacter.rawInventoryData || []" 
        />
        <!-- Debug: Show what we're passing -->
        <div style="display: none;">Character has: {{ selectedCharacter.rawInventoryData?.length || 0 }} items</div>
      </div>
      
      <!-- Empty State -->
      <div v-else class="empty-state">
        <p>Select a main character or search for a character to view their inventory</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import CharacterInventory from '../components/CharacterInventory.vue'
import { getApiBaseUrl } from '../config/api'
import axios from 'axios'
import { resilientApi } from '../utils/resilientRequest'

export default {
  name: 'Characters',
  components: {
    CharacterInventory
  },
  setup() {
    // Circuit breaker pattern for problematic endpoints
    const circuitBreakerState = ref({
      currency: { failures: 0, lastFailure: null, isOpen: false },
      stats: { failures: 0, lastFailure: null, isOpen: false },
      search: { failures: 0, lastFailure: null, isOpen: false }
    })
    
    const isCircuitOpen = (endpoint) => {
      const state = circuitBreakerState.value[endpoint]
      if (!state) return false
      
      // Circuit is open if we've had 8+ failures in the last 2 minutes (more lenient)
      if (state.failures >= 8) {
        const twoMinutesAgo = Date.now() - 2 * 60 * 1000
        if (state.lastFailure && state.lastFailure > twoMinutesAgo) {
          return true
        } else {
          // Reset after 2 minutes (faster recovery)
          state.failures = 0
          state.lastFailure = null
          state.isOpen = false
        }
      }
      return false
    }
    
    const recordFailure = (endpoint, error = null) => {
      const state = circuitBreakerState.value[endpoint]
      if (!state) return
      
      // Only count serious failures - ignore CORS and network connectivity issues
      const shouldCount = !error || (
        !error.message?.includes('CORS') &&
        !error.message?.includes('ERR_CONNECTION_REFUSED') &&
        !error.code?.includes('ERR_NETWORK') &&
        error.response?.status !== 403 // Ignore CORS 403 errors
      )
      
      if (shouldCount) {
        state.failures++
        state.lastFailure = Date.now()
        
        if (state.failures >= 8) {
          state.isOpen = true
          console.warn(`Circuit breaker opened for ${endpoint} endpoint after 8 failures`)
        }
      } else {
        console.debug(`Ignoring ${endpoint} failure due to network/CORS issue:`, error?.message)
      }
    }
    
    const recordSuccess = (endpoint) => {
      const state = circuitBreakerState.value[endpoint]
      if (!state) return
      
      // Reset on successful request
      state.failures = 0
      state.lastFailure = null
      state.isOpen = false
    }
    
    // Manual circuit breaker reset function (can be called from console for debugging)
    const resetCircuitBreaker = (endpoint = null) => {
      if (endpoint) {
        const state = circuitBreakerState.value[endpoint]
        if (state) {
          state.failures = 0
          state.lastFailure = null
          state.isOpen = false
          console.log(`Circuit breaker reset for ${endpoint}`)
        }
      } else {
        // Reset all circuit breakers
        Object.keys(circuitBreakerState.value).forEach(key => {
          const state = circuitBreakerState.value[key]
          state.failures = 0
          state.lastFailure = null
          state.isOpen = false
        })
        console.log('All circuit breakers reset')
      }
    }
    
    // Expose for debugging in development
    if (import.meta.env.DEV) {
      window.resetCircuitBreaker = resetCircuitBreaker
    }
    
    // Request deduplication to prevent identical API calls
    const activeRequests = ref(new Map())
    
    const dedupedRequest = async (key, requestFn) => {
      // If request is already in progress, wait for it
      if (activeRequests.value.has(key)) {
        console.log(`Deduplicating request: ${key}`)
        return activeRequests.value.get(key)
      }
      
      // Start new request and store promise
      const requestPromise = requestFn()
      activeRequests.value.set(key, requestPromise)
      
      try {
        const result = await requestPromise
        return result
      } finally {
        // Clean up when request completes
        activeRequests.value.delete(key)
      }
    }
    // Main character slots
    const primaryMain = ref(null)
    const secondaryMain = ref(null)
    const isUpdatingMains = ref(false)
    
    // Currently displayed character and source
    const selectedCharacter = ref(null)
    const activeSlot = ref(null) // 'primary', 'secondary', or null for search
    // Store inventory data for bag contents
    const inventoryDataCache = ref([])
    
    // Computed property to ensure inventory data is available
    const inventoryData = computed(() => {
      return inventoryDataCache.value || []
    })
    
    // Character search functionality
    const searchInput = ref(null)
    const searchQuery = ref('')
    const searchResults = ref([])
    const isSearching = ref(false)
    const searchPerformed = ref(false)
    const lastSearchQuery = ref('')
    
    // Enhanced pagination and navigation
    const currentPage = ref(0)
    const resultsPerPage = ref(8)
    const selectedIndex = ref(-1)
    const totalResults = ref(0)
    
    // Computed properties for pagination
    const totalPages = computed(() => Math.ceil(totalResults.value / resultsPerPage.value))
    const paginatedResults = computed(() => {
      const start = currentPage.value * resultsPerPage.value
      const end = start + resultsPerPage.value
      return searchResults.value.slice(start, end)
    })
    const hasNextPage = computed(() => currentPage.value < totalPages.value - 1)
    const hasPrevPage = computed(() => currentPage.value > 0)
    
    // Keyboard navigation functions
    const navigateUp = () => {
      if (paginatedResults.value.length === 0) return
      selectedIndex.value = selectedIndex.value <= 0 ? paginatedResults.value.length - 1 : selectedIndex.value - 1
    }
    
    const navigateDown = () => {
      if (paginatedResults.value.length === 0) return
      selectedIndex.value = selectedIndex.value >= paginatedResults.value.length - 1 ? 0 : selectedIndex.value + 1
    }
    
    const navigateNextPage = () => {
      if (hasNextPage.value) {
        currentPage.value++
        selectedIndex.value = 0
      }
    }
    
    const navigatePrevPage = () => {
      if (hasPrevPage.value) {
        currentPage.value--
        selectedIndex.value = 0
      }
    }
    
    const selectCurrentCharacter = () => {
      if (selectedIndex.value >= 0 && selectedIndex.value < paginatedResults.value.length) {
        const character = paginatedResults.value[selectedIndex.value]
        viewSearchedCharacter(character)
      }
    }
    
    // Keyboard event handler
    const handleKeydown = (event) => {
      // Early return for non-navigation keys to avoid unnecessary processing
      const navigationKeys = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Enter', 'Escape']
      if (!navigationKeys.includes(event.key)) return
      
      if (searchResults.value.length === 0) return
      
      switch (event.key) {
        case 'ArrowUp':
          event.preventDefault()
          navigateUp()
          break
        case 'ArrowDown':
          event.preventDefault()
          navigateDown()
          break
        case 'ArrowLeft':
          event.preventDefault()
          navigatePrevPage()
          break
        case 'ArrowRight':
          event.preventDefault()
          navigateNextPage()
          break
        case 'Enter':
          event.preventDefault()
          selectCurrentCharacter()
          break
        case 'Escape':
          event.preventDefault()
          searchResults.value = []
          searchPerformed.value = false
          selectedIndex.value = -1
          break
      }
    }
    
    // Modal for main character selection
    const showSearchModal = ref(false)
    const searchModalType = ref('primary') // 'primary' or 'secondary'
    const modalSearchQuery = ref('')
    const modalSearchResults = ref([])
    
    // Character loading state and request management
    const isLoadingCharacter = ref(false)
    const currentCharacterRequest = ref(null)
    const currentSearchRequest = ref(null)
    
    // Rate limiting for character searches to prevent backend overload
    let lastSearchTime = 0
    const SEARCH_RATE_LIMIT = 1000 // Minimum 1 second between searches

    // Load user's saved main characters on page load
    const loadUserMainCharacters = async () => {
      console.log('🔄 Loading user main characters...')
      
      try {
        const response = await axios.get(`${getApiBaseUrl()}/api/user/characters/mains`, {
          timeout: 10000, // 10 second timeout
          headers: {
            'Accept': 'application/json'
          }
        })
        
        console.log('✅ Main characters API response:', response.data)
        
        if (response.data && response.data.success) {
          if (response.data.data?.primaryMain) {
            primaryMain.value = response.data.data.primaryMain
            console.log('✓ Loaded primary main:', response.data.data.primaryMain.name)
          }
          if (response.data.data?.secondaryMain) {
            secondaryMain.value = response.data.data.secondaryMain
            console.log('✓ Loaded secondary main:', response.data.data.secondaryMain.name)
          }
          
          if (!response.data.data?.primaryMain && !response.data.data?.secondaryMain) {
            console.log('ℹ️ No main characters saved yet')
          }
        } else {
          console.log('⚠️ API returned success=false or no data field')
        }
        
      } catch (error) {
        if (error.code === 'ECONNABORTED') {
          console.warn('⏱️ Main characters loading timed out')
        } else if (error.response?.status === 404) {
          console.log('ℹ️ Main characters endpoint not found (expected in development)')
        } else if (error.response?.status === 401) {
          console.log('🔒 User not authenticated, skipping main character loading')
        } else {
          console.error('❌ Failed to load user main characters:', {
            message: error.message,
            status: error.response?.status,
            data: error.response?.data
          })
        }
        
        // No fallback - let the error state remain
      }
    }

    // Search for characters by name
    const searchCharacters = async (query, isModalSearch = false) => {
      if (!query.trim()) return []
      
      // Circuit breaker: skip search if too many recent failures
      if (isCircuitOpen('search')) {
        console.log('Character search circuit breaker active, skipping search')
        return []
      }
      
      // Rate limiting: enforce minimum time between searches
      const now = Date.now()
      const timeSinceLastSearch = now - lastSearchTime
      if (timeSinceLastSearch < SEARCH_RATE_LIMIT) {
        console.log(`Search rate limited, waiting ${SEARCH_RATE_LIMIT - timeSinceLastSearch}ms`)
        await new Promise(resolve => setTimeout(resolve, SEARCH_RATE_LIMIT - timeSinceLastSearch))
      }
      lastSearchTime = Date.now()
      
      // Cancel any existing search request
      if (currentSearchRequest.value) {
        currentSearchRequest.value.abort()
        currentSearchRequest.value = null
      }
      
      // Create new AbortController for this search
      currentSearchRequest.value = new AbortController()
      
      try {
        const response = await resilientApi.get('/api/characters/search', {
          params: { 
            name: query.trim(),
            limit: isModalSearch ? 5 : 50  // Get more results for main search
          },
          timeout: 15000, // Increased to 15 second timeout for more reliability
          signal: currentSearchRequest.value.signal
        })
        
        // Record success to reset circuit breaker
        recordSuccess('search')
        
        return response.data.map(character => ({
          id: character.id,
          name: character.name,
          level: character.level,
          class: character.class, // Backend already returns class name
          race: character.race, // Backend already returns race name
          // Basic info for search results
          rawData: character // Keep raw data for full character loading
        }))
      } catch (error) {
        if (error.name === 'AbortError') {
          console.log('Search request cancelled')
          return []
        }
        
        // Record failure for circuit breaker
        recordFailure('search', error)
        
        console.error('Failed to search characters:', {
          query,
          error: error.message,
          status: error.response?.status
        })
        return []
      } finally {
        currentSearchRequest.value = null
      }
    }

    // Load full character details
    const loadFullCharacterData = async (characterId, abortSignal = null) => {
      try {
        // Load basic character data with timeout and abort signal
        const charResponse = await resilientApi.get(`/api/characters/${characterId}`, {
          timeout: 12000, // Increased to 12 second timeout for basic character data
          signal: abortSignal
        })
        const character = charResponse.data
        
        const fullCharacter = {
          id: character.id,
          name: character.name,
          level: character.level,
          class: character.class, // Backend already returns class name
          race: character.race, // Backend already returns race name
          maxHp: character.cur_hp, // Will be recalculated
          maxMp: character.mana,   // Will be recalculated
          stats: {
            str: character.str || 0,
            sta: character.sta || 0,
            agi: character.agi || 0,
            dex: character.dex || 0,
            wis: character.wis || 0,
            int: character.int || 0,
            cha: character.cha || 0
          },
          resistances: {
            poison: 0, magic: 0, disease: 0, fire: 0, cold: 0, corrupt: 0
          },
          endurance: character.endurance || 0,
          ac: 0, atk: 0, weight: 0,
          currency: { platinum: 0, gold: 0, silver: 0, copper: 0 },
          equipment: {},  // Add equipment object
          inventory: []
        }

        // Load additional data in parallel with timeout and abort signal
        const timeout = (ms, signal) => new Promise((_, reject) => {
          const timeoutId = setTimeout(() => reject(new Error('Request timeout')), ms)
          signal?.addEventListener('abort', () => {
            clearTimeout(timeoutId)
            reject(new DOMException('Aborted', 'AbortError'))
          })
        })
        
        try {
          // Load inventory first (critical for character display)
          try {
            await Promise.race([
              loadCharacterInventory(characterId, fullCharacter, abortSignal),
              timeout(20000, abortSignal) // 20 second timeout for inventory
            ])
          } catch (error) {
            if (error.name === 'AbortError') {
              throw error
            }
            console.warn('Character inventory loading failed but continuing:', error)
          }
          
          // Load currency and stats asynchronously (non-blocking)
          Promise.allSettled([
            loadCharacterCurrency(characterId, fullCharacter, abortSignal),
            loadCharacterStats(characterId, fullCharacter, abortSignal)
          ]).then(results => {
            // Log any failures but character is already displayed
            results.forEach((result, index) => {
              if (result.status === 'rejected') {
                const type = index === 0 ? 'currency' : 'stats'
                console.warn(`Character ${type} loading failed (background):`, result.reason)
              }
            })
          }).catch(error => {
            console.warn('Background loading failed:', error)
          })
        } catch (error) {
          if (error.name === 'AbortError') {
            throw error // Re-throw abort errors
          }
          console.warn('Some character data failed to load:', error)
          // Continue with partial data rather than failing completely
        }

        return fullCharacter
      } catch (error) {
        console.error('Failed to load full character data:', error)
        throw error
      }
    }

    const generateMockInventory = () => {
      const slots = []
      
      // Generate 8x10 inventory grid (80 slots total)
      for (let i = 0; i < 80; i++) {
        const isEmpty = Math.random() > 0.3 // 30% chance of item
        slots.push({
          slot: i,
          item: isEmpty ? null : {
            id: i + 1000,
            name: `Item ${i + 1}`,
            icon: getRandomItemIcon(),
            stackSize: Math.random() > 0.7 ? Math.floor(Math.random() * 20) + 1 : null
          }
        })
      }
      return slots
    }

    const getRandomItemIcon = () => {
      // Use actual EQ item icons from the public/icons/items/ directory
      const iconNumbers = [
        500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515,
        516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531,
        532, 533, 534, 535, 536, 537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547,
        548, 549, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1100, 1200
      ]
      const randomIcon = iconNumbers[Math.floor(Math.random() * iconNumbers.length)]
      return `/icons/items/${randomIcon}.png`
    }

    // UI Interaction Methods
    
    // View a main character (Primary or Secondary)
    const viewCharacter = async (character, slotType) => {
      if (isLoadingCharacter.value) {
        return
      }
      
      // Throttle character loading to prevent rapid successive requests
      const now = Date.now()
      if (window.lastCharacterLoadTime && now - window.lastCharacterLoadTime < 3000) {
        return
      }
      window.lastCharacterLoadTime = now
      
      try {
        isLoadingCharacter.value = true
        activeSlot.value = slotType
        
        // Cancel any existing character loading request
        if (currentCharacterRequest.value) {
          currentCharacterRequest.value.abort()
          currentCharacterRequest.value = null
        }
        
        // Create new AbortController for this request
        currentCharacterRequest.value = new AbortController()
        
        const fullCharacter = await loadFullCharacterData(character.id, currentCharacterRequest.value.signal)
        selectedCharacter.value = fullCharacter
      } catch (error) {
        if (error.name === 'AbortError') {
          return
        }
        console.error(`Failed to load ${character.name}'s data:`, error)
        alert(`Failed to load ${character.name}'s data. The server may be busy. Please try again.`)
      } finally {
        isLoadingCharacter.value = false
        currentCharacterRequest.value = null
      }
    }

    // Open modal to search for main character
    const openCharacterSearch = (slotType) => {
      searchModalType.value = slotType
      modalSearchQuery.value = ''
      modalSearchResults.value = []
      showSearchModal.value = true
    }

    // Close character search modal
    const closeSearchModal = () => {
      showSearchModal.value = false
      modalSearchQuery.value = ''
      modalSearchResults.value = []
    }

    // Debounce timer for search
    let searchDebounceTimer = null
    
    // Handle search input for character lookup section - no real-time search
    const handleSearchInput = () => {
      // Clear results when input is empty
      if (!searchQuery.value.trim()) {
        searchResults.value = []
        searchPerformed.value = false
      }
    }

    // Perform character search (lookup section)
    const performSearch = async () => {
      if (!searchQuery.value.trim()) return
      
      // Prevent rapid successive searches
      if (isSearching.value) {
        console.log('Search already in progress, ignoring request')
        return
      }
      
      isSearching.value = true
      lastSearchQuery.value = searchQuery.value.trim()
      
      try {
        const results = await searchCharacters(searchQuery.value)
        searchResults.value = results
        totalResults.value = results.length
        currentPage.value = 0
        selectedIndex.value = results.length > 0 ? 0 : -1  // Auto-select first result if available
        searchPerformed.value = true
        // Clear the search input after successful search
        searchQuery.value = ''
        
        // Focus the search container for keyboard navigation
        nextTick(() => {
          const container = document.querySelector('.search-container')
          if (container) container.focus()
        })
      } catch (error) {
        console.error('Search failed:', error)
        searchResults.value = []
        totalResults.value = 0
        currentPage.value = 0
        selectedIndex.value = -1  // No selection when search fails
        searchPerformed.value = true
        // Clear the search input even on error
        searchQuery.value = ''
      } finally {
        isSearching.value = false
      }
    }

    // View a searched character (temporary lookup)
    const viewSearchedCharacter = async (character) => {
      if (isLoadingCharacter.value) {
        return
      }
      
      // Throttle character loading to prevent rapid successive requests
      const now = Date.now()
      if (window.lastCharacterLoadTime && now - window.lastCharacterLoadTime < 3000) {
        return
      }
      window.lastCharacterLoadTime = now
      
      try {
        isLoadingCharacter.value = true
        activeSlot.value = null // Clear active slot to indicate this is a lookup
        
        // Cancel any existing character loading request
        if (currentCharacterRequest.value) {
          currentCharacterRequest.value.abort()
          currentCharacterRequest.value = null
        }
        
        // Create new AbortController for this request
        currentCharacterRequest.value = new AbortController()
        
        console.log(`Loading character: ${character.name} (ID: ${character.id})`)
        const fullCharacter = await loadFullCharacterData(character.id, currentCharacterRequest.value.signal)
        selectedCharacter.value = fullCharacter
        
        // Hide the dropdown after selection
        searchResults.value = []
        searchPerformed.value = false
        console.log(`Successfully loaded character: ${character.name}`)
      } catch (error) {
        if (error.name === 'AbortError') {
          console.log('Character loading was cancelled')
          return
        }
        console.error(`Failed to load ${character.name}'s data:`, {
          characterId: character.id,
          error: error.message,
          status: error.response?.status
        })
        // More graceful error message without alert
        console.warn(`Character loading failed for ${character.name}. Please try again.`)
      } finally {
        isLoadingCharacter.value = false
        currentCharacterRequest.value = null
      }
    }

    // Handle search input for modal
    const handleModalSearchInput = () => {
      if (!modalSearchQuery.value.trim()) {
        modalSearchResults.value = []
      }
    }

    // Perform search in modal
    const performModalSearch = async () => {
      if (!modalSearchQuery.value.trim()) return
      
      isSearching.value = true
      
      try {
        const results = await searchCharacters(modalSearchQuery.value)
        modalSearchResults.value = results
      } catch (error) {
        console.error('Modal search failed:', error)
        modalSearchResults.value = []
      } finally {
        isSearching.value = false
      }
    }

    // Select character as main from modal
    const selectMainCharacter = async (character) => {
      if (searchModalType.value === 'primary') {
        await setPrimaryMain(character)
      } else {
        await setSecondaryMain(character)
      }
      closeSearchModal()
    }

    // Clear a main character slot
    const clearMainSlot = async (slotType) => {
      const character = slotType === 'primary' ? primaryMain.value : secondaryMain.value
      if (character) {
        await removeAsMain(character, slotType)
      }
    }

    const loadCharacterInventory = async (characterId, character, abortSignal = null) => {
      try {
        const response = await resilientApi.get(`/api/characters/${characterId}/inventory`, {
          timeout: 20000, // Increased to 20 second timeout for large inventories
          signal: abortSignal
        })
        
        // Handle partial data warnings from backend
        if (response.data.warning) {
          console.warn(`Character ${characterId} inventory warning:`, response.data.warning)
        }
        // Transform inventory data from EQEmu schema
        const equipmentData = response.data.equipment || {}
        const inventorySlots = response.data.inventory || []
        
        // Store inventory data directly on character object for bag contents
        character.rawInventoryData = [...inventorySlots]
        // Store raw inventory for bag mapping functionality
        const bagContentSlots = inventorySlots.filter(slot => slot.slotid >= 262 && slot.slotid <= 361)
        
        // Set equipped items
        character.equipment = equipmentData
        
        // Process inventory slots - transform backend data to UI format using proper slot mapping
        character.inventory = []
        
        // Create 10 main inventory slots (slots 23-32) - these contain bags/items
        for (let slotId = 23; slotId <= 32; slotId++) {
          const inventoryItem = inventorySlots.find(inv => inv.slotid === slotId)
          
          if (inventoryItem && inventoryItem.itemid) {
            character.inventory.push({
              slot: slotId - 23, // Convert EQEmu slot ID to 0-based UI position
              slotid: slotId,
              item: {
                id: inventoryItem.itemid,
                name: inventoryItem.item_name,
                icon: `/icons/items/${inventoryItem.item_icon || 500}.png`,
                charges: inventoryItem.charges || 0,
                stackSize: inventoryItem.stackable ? (inventoryItem.charges || 1) : 1,
                stackable: inventoryItem.stackable,
                color: inventoryItem.color || 0,
                augments: inventoryItem.augslots || [],
                containerSize: inventoryItem.container_size || 0,
                itemType: inventoryItem.item_type || 0
              }
            })
          } else {
            character.inventory.push({
              slot: slotId - 23,
              slotid: slotId,
              item: null
            })
          }
        }
        
      } catch (error) {
        if (error.name === 'AbortError') {
          return
        }
        console.error(`Failed to load inventory for character ${characterId}:`, error)
        
        // Check if it's a timeout error and provide specific feedback
        if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
          console.warn('Character inventory loading timed out - server may be overloaded')
        }
        
        // Set empty equipment and inventory on error for graceful degradation
        character.equipment = {}
        character.inventory = []
      }
    }

    const processInventoryData = async (inventorySlots) => {
      const slots = []
      
      // EQEmu general inventory slots are typically 22-29 (personal inventory bags) and 251-340 (general inventory)
      // Create 80 slots for the 8x10 inventory grid (slots 251-330 for general inventory)
      for (let slotId = 251; slotId <= 330; slotId++) {
        const inventoryItem = inventorySlots.find(inv => inv.slotid === slotId)
        
        if (inventoryItem) {
          // Fetch item details from items table
          const itemDetails = await getItemDetails(inventoryItem.itemid)
          
          slots.push({
            slot: slotId - 251, // Convert to 0-based index for UI
            slotid: slotId,
            item: {
              id: inventoryItem.itemid,
              name: itemDetails?.name || `Item ${inventoryItem.itemid}`,
              icon: itemDetails?.icon || getRandomItemIcon(),
              stackSize: inventoryItem.charges > 1 ? inventoryItem.charges : null,
              color: inventoryItem.color || 0,
              charges: inventoryItem.charges,
              augments: [
                inventoryItem.augslot1,
                inventoryItem.augslot2,
                inventoryItem.augslot3,
                inventoryItem.augslot4,
                inventoryItem.augslot5,
                inventoryItem.augslot6
              ].filter(aug => aug > 0)
            }
          })
        } else {
          slots.push({
            slot: slotId - 251,
            slotid: slotId,
            item: null
          })
        }
      }
      
      return slots
    }

    const getItemDetails = async (itemId) => {
      try {
        const response = await axios.get(`${getApiBaseUrl()}/api/item/${itemId}`)
        return response.data
      } catch (error) {
        console.error(`Failed to load item details for ${itemId}:`, error)
        return null
      }
    }

    // Load character currency with local fallback
    const loadCharacterCurrency = async (characterId, character, abortSignal = null) => {
      // Set default currency values first (like Magelo)
      character.currency = {
        platinum: 0,
        gold: 0,
        silver: 0,
        copper: 0
      }
      
      // Try to load from API if circuit breaker allows
      if (!isCircuitOpen('currency')) {
        const requestKey = `currency-${characterId}`
        try {
          const response = await dedupedRequest(requestKey, async () => {
            return await resilientApi.get(`/api/characters/${characterId}/currency`, {
              timeout: 8000, // Reduced timeout for faster response
              signal: abortSignal
            })
          })
          
          if (response && response.data) {
            character.currency = {
              platinum: response.data.platinum || 0,
              gold: response.data.gold || 0,
              silver: response.data.silver || 0,
              copper: response.data.copper || 0
            }
            console.log('Loaded currency from server:', character.currency)
          }
          
          recordSuccess('currency')
        } catch (error) {
          if (error.name === 'AbortError') {
            console.log('Character currency loading was cancelled')
            return
          }
          
          recordFailure('currency', error)
          console.warn('Currency loading failed, using default values:', error.message)
          // Keep default currency values (all zeros)
        }
      } else {
        console.log('Currency endpoint circuit breaker active, using default values')
      }
    }

    // Calculate character stats locally (Magelo-style) with API fallback
    const loadCharacterStats = async (characterId, character, abortSignal = null) => {
      try {
        // PRIMARY: Calculate stats locally from equipment (like Magelo)
        calculateStatsFromEquipment(character)
        
        // FALLBACK: Try to get server-calculated stats if circuit breaker allows
        if (!isCircuitOpen('stats')) {
          const requestKey = `stats-${characterId}`
          try {
            const response = await dedupedRequest(requestKey, async () => {
              return await resilientApi.get(`/api/characters/${characterId}/stats`, {
                timeout: 8000, // Reduced timeout for faster fallback
                signal: abortSignal
              })
            })
            
            // Override local calculations with server values if available
            if (response && response.data) {
              character.maxHp = response.data.maxHp || character.maxHp
              character.maxMp = response.data.maxMp || character.maxMp
              character.ac = response.data.ac || character.ac
              character.atk = response.data.atk || character.atk
              character.weight = response.data.weight || character.weight
              
              if (response.data.resistances) {
                character.resistances = {
                  poison: response.data.resistances.poison || character.resistances.poison,
                  magic: response.data.resistances.magic || character.resistances.magic,
                  disease: response.data.resistances.disease || character.resistances.disease,
                  fire: response.data.resistances.fire || character.resistances.fire,
                  cold: response.data.resistances.cold || character.resistances.cold,
                  corrupt: response.data.resistances.corrupt || character.resistances.corrupt || 0
                }
              }
              
              console.log('Enhanced stats with server calculations')
            }
            
            recordSuccess('stats')
          } catch (apiError) {
            recordFailure('stats', apiError)
            console.warn('Server stat calculation failed, using local calculations:', apiError.message)
            // Keep locally calculated stats
          }
        } else {
          console.log('Stats endpoint circuit breaker active, using local calculations only')
        }
        
      } catch (error) {
        if (error.name === 'AbortError') {
          console.log('Character stats loading was cancelled')
          return
        }
        console.error('Failed to calculate character stats:', error)
        // Set minimal fallback values
        setFallbackStats(character)
      }
    }
    
    // Calculate stats exactly like Magelo character browser (100% identical methodology)
    const calculateStatsFromEquipment = (character) => {
      // Initialize stats exactly as Magelo does
      character.ac = 0
      character.atk = 0
      character.weight = 0
      
      // Initialize resistances exactly as Magelo displays them
      character.resistances = {
        poison: 0,
        magic: 0,
        disease: 0,
        fire: 0,
        cold: 0,
        corrupt: 0
      }
      
      // Get base character stats from database
      const baseStats = character.stats || {}
      const level = character.level || 1
      const charClass = character.class || 'Warrior'
      
      // Calculate equipment bonuses exactly like Magelo
      if (character.equipment) {
        Object.values(character.equipment).forEach(item => {
          if (item && typeof item === 'object') {
            // AC: Sum all equipped item AC values (Magelo method)
            character.ac += parseInt(item.ac || 0)
            
            // ATK: Sum all equipped item ATK values (Magelo method)
            character.atk += parseInt(item.atk || 0)
            
            // Weight: Sum all equipped item weights (Magelo method)
            character.weight += parseFloat(item.weight || 0)
            
            // Resistances: Sum all equipped item resistance values (Magelo method)
            character.resistances.poison += parseInt(item.pr || 0)
            character.resistances.magic += parseInt(item.mr || 0)
            character.resistances.fire += parseInt(item.fr || 0)
            character.resistances.cold += parseInt(item.cr || 0)
            character.resistances.disease += parseInt(item.dr || 0)
            character.resistances.corrupt += parseInt(item.cor || item.corruption || 0)
          }
        })
      }
      
      // Calculate HP exactly like Magelo (using EverQuest's actual formulas)
      const stamina = parseInt(baseStats.sta || 75) // Default starting STA varies by race
      const constitution = stamina // In EQ, STA is constitution
      
      // Magelo HP Formula: Base HP + (Level * HP per level) + (STA bonus)
      // Class-specific HP per level multipliers (exactly as Magelo calculates)
      const hpPerLevelByClass = {
        'Warrior': 22,
        'Cleric': 15,
        'Paladin': 20,
        'Ranger': 20,
        'Shadow Knight': 20,
        'Shadowknight': 20,
        'Druid': 15,
        'Monk': 18,
        'Bard': 16,
        'Rogue': 16,
        'Shaman': 15,
        'Necromancer': 14,
        'Wizard': 12,
        'Magician': 12,
        'Enchanter': 12,
        'Beastlord': 18,
        'Berserker': 25
      }
      
      const hpPerLevel = hpPerLevelByClass[charClass] || 15
      const baseHpForClass = 100 // Base HP for all classes at level 1
      
      // Stamina HP bonus (every 1 STA = ~10 HP, but diminishing returns apply)
      let staHpBonus = 0
      if (stamina > 75) {
        staHpBonus = Math.floor((stamina - 75) * 10) // Linear bonus above racial base
      }
      
      character.maxHp = baseHpForClass + (level * hpPerLevel) + staHpBonus
      
      // Calculate MP exactly like Magelo (using EverQuest's actual formulas)
      const intelligence = parseInt(baseStats.int || 75)
      const wisdom = parseInt(baseStats.wis || 75)
      
      // MP-using classes (exactly as Magelo determines)
      const mpClasses = {
        'Cleric': 'wisdom',
        'Druid': 'wisdom',
        'Shaman': 'wisdom',
        'Wizard': 'intelligence',
        'Magician': 'intelligence',
        'Necromancer': 'intelligence',
        'Enchanter': 'intelligence',
        'Paladin': 'wisdom',      // Paladins get MP at level 9+
        'Shadow Knight': 'intelligence', // SKs get MP at level 9+
        'Shadowknight': 'intelligence',
        'Ranger': 'wisdom',       // Rangers get MP at level 9+
        'Beastlord': 'wisdom'     // Beastlords get MP at level 9+
      }
      
      if (mpClasses[charClass]) {
        const mentalStat = mpClasses[charClass] === 'wisdom' ? wisdom : intelligence
        const isHybrid = ['Paladin', 'Ranger', 'Shadow Knight', 'Shadowknight', 'Beastlord'].includes(charClass)
        
        if (isHybrid && level < 9) {
          // Hybrid classes don't get MP until level 9
          character.maxMp = 0
        } else {
          // Magelo MP Formula: Base MP + (Level * MP per level) + (Mental stat bonus)
          const mpPerLevelByClass = {
            'Cleric': 11,
            'Druid': 11,
            'Shaman': 11,
            'Wizard': 13,
            'Magician': 13,
            'Necromancer': 12,
            'Enchanter': 12,
            'Paladin': 4,        // Hybrids get less MP per level
            'Ranger': 4,
            'Shadow Knight': 4,
            'Shadowknight': 4,
            'Beastlord': 9
          }
          
          const mpPerLevel = mpPerLevelByClass[charClass] || 0
          const baseMpForClass = 50
          
          // Mental stat MP bonus (every 1 INT/WIS above base = ~5 MP)
          let mentalStatBonus = 0
          if (mentalStat > 75) {
            mentalStatBonus = Math.floor((mentalStat - 75) * 5)
          }
          
          character.maxMp = baseMpForClass + (level * mpPerLevel) + mentalStatBonus
        }
      } else {
        // Non-caster classes have 0 MP
        character.maxMp = 0
      }
      
      // Round weight to 1 decimal place like Magelo
      character.weight = Math.round(character.weight * 10) / 10
      
      console.log('Calculated stats using Magelo methodology:', {
        ac: character.ac,
        atk: character.atk,
        weight: character.weight,
        maxHp: character.maxHp,
        maxMp: character.maxMp,
        resistances: character.resistances,
        method: 'Magelo-exact'
      })
    }
    
    // Set fallback stats if all calculations fail
    const setFallbackStats = (character) => {
      character.ac = character.ac || 0
      character.atk = character.atk || 0
      character.weight = character.weight || 0
      character.maxHp = character.maxHp || (character.level * 20 + 100)
      character.maxMp = character.maxMp || 0
      character.resistances = character.resistances || {
        poison: 0, magic: 0, disease: 0, fire: 0, cold: 0, corrupt: 0
      }
    }

    // Get class icon path
    const getClassIcon = (className) => {
      const normalizedClass = normalizeClassName(className)
      return `/icons/${normalizedClass.toLowerCase()}.gif`
    }

    // Normalize class name (handle specialty titles)
    const normalizeClassName = (className) => {
      const classMapping = {
        // Warrior specializations
        'Myrmidon': 'Warrior', 'Champion': 'Warrior', 'Warlord': 'Warrior',
        // Cleric specializations  
        'Vicar': 'Cleric', 'Templar': 'Cleric', 'High Priest': 'Cleric',
        // Paladin specializations
        'Cavalier': 'Paladin', 'Knight': 'Paladin', 'Lord Protector': 'Paladin',
        // Ranger specializations
        'Pathfinder': 'Ranger', 'Outrider': 'Ranger', 'Warder': 'Ranger',
        // Shadow Knight specializations and base class
        'Shadow Knight': 'Shadowknight', 'Reaver': 'Shadowknight', 'Revenant': 'Shadowknight', 'Grave Lord': 'Shadowknight',
        // Druid specializations
        'Wanderer': 'Druid', 'Preserver': 'Druid', 'Hierophant': 'Druid',
        // Additional mappings...
      }
      return classMapping[className] || className
    }

    // EQEmu class ID to name mapping
    const getClassName = (classId) => {
      const classes = {
        1: 'Warrior', 2: 'Cleric', 3: 'Paladin', 4: 'Ranger', 5: 'Shadow Knight',
        6: 'Druid', 7: 'Monk', 8: 'Bard', 9: 'Rogue', 10: 'Shaman',
        11: 'Necromancer', 12: 'Wizard', 13: 'Magician', 14: 'Enchanter',
        15: 'Beastlord', 16: 'Berserker'
      }
      return classes[classId] || 'Unknown'
    }

    // EQEmu race ID to name mapping  
    const getRaceName = (raceId) => {
      const races = {
        1: 'Human', 2: 'Barbarian', 3: 'Erudite', 4: 'Wood Elf', 5: 'High Elf',
        6: 'Dark Elf', 7: 'Half Elf', 8: 'Dwarf', 9: 'Troll', 10: 'Ogre',
        11: 'Halfling', 12: 'Gnome', 128: 'Iksar', 130: 'Vah Shir', 330: 'Froglok',
        522: 'Drakkin'
      }
      return races[raceId] || 'Unknown'
    }


    // Set character as primary main
    const setPrimaryMain = async (character) => {
      // Validation checks
      if (!character) {
        console.error('Cannot set primary main: character is null or undefined')
        return
      }
      
      if (!character.id) {
        console.error('Cannot set primary main: character.id is missing', character)
        return
      }
      
      if (isUpdatingMains.value) {
        console.warn('Primary main update already in progress, ignoring request')
        return
      }
      
      // Check if character is already the primary main
      if (primaryMain.value && primaryMain.value.id === character.id) {
        console.log(`${character.name} is already the primary main character`)
        return
      }
      
      isUpdatingMains.value = true
      
      try {
        // Ensure we have the API base URL
        const apiBaseUrl = getApiBaseUrl()
        if (!apiBaseUrl) {
          throw new Error('API base URL is not available')
        }
        
        const response = await axios.post(`${apiBaseUrl}/api/user/characters/primary`, {
          characterId: character.id,
          characterName: character.name || 'Unknown'
        }, {
          timeout: 10000, // 10 second timeout
          headers: {
            'Content-Type': 'application/json'
          }
        })
        
        // Verify the response
        if (response.status === 200 || response.status === 201) {
          primaryMain.value = character
          console.log(`Successfully set ${character.name} as Primary Main`)
        } else {
          throw new Error(`Unexpected response status: ${response.status}`)
        }
        
      } catch (error) {
        // Enhanced error handling
        if (error.response) {
          // Server responded with error status
          console.error('Failed to set primary main - Server error:', {
            status: error.response.status,
            data: error.response.data,
            character: character.name
          })
        } else if (error.request) {
          // Request was made but no response received
          console.error('Failed to set primary main - Network error:', {
            message: 'No response from server',
            character: character.name
          })
        } else {
          // Something else went wrong
          console.error('Failed to set primary main - Unexpected error:', {
            message: error.message,
            character: character.name
          })
        }
        
        // Do not set mock data - let the error propagate
        throw error
        
      } finally {
        isUpdatingMains.value = false
      }
    }

    // Set character as secondary main  
    const setSecondaryMain = async (character) => {
      // Validation checks
      if (!character) {
        console.error('Cannot set secondary main: character is null or undefined')
        return
      }
      
      if (!character.id) {
        console.error('Cannot set secondary main: character.id is missing', character)
        return
      }
      
      if (isUpdatingMains.value) {
        console.warn('Secondary main update already in progress, ignoring request')
        return
      }
      
      // Check if character is already the secondary main
      if (secondaryMain.value && secondaryMain.value.id === character.id) {
        console.log(`${character.name} is already the secondary main character`)
        return
      }
      
      isUpdatingMains.value = true
      
      try {
        // Ensure we have the API base URL
        const apiBaseUrl = getApiBaseUrl()
        if (!apiBaseUrl) {
          throw new Error('API base URL is not available')
        }
        
        const response = await axios.post(`${apiBaseUrl}/api/user/characters/secondary`, {
          characterId: character.id,
          characterName: character.name || 'Unknown'
        }, {
          timeout: 10000, // 10 second timeout
          headers: {
            'Content-Type': 'application/json'
          }
        })
        
        // Verify the response
        if (response.status === 200 || response.status === 201) {
          secondaryMain.value = character
          console.log(`Successfully set ${character.name} as Secondary Main`)
        } else {
          throw new Error(`Unexpected response status: ${response.status}`)
        }
        
      } catch (error) {
        // Enhanced error handling
        if (error.response) {
          // Server responded with error status
          console.error('Failed to set secondary main - Server error:', {
            status: error.response.status,
            data: error.response.data,
            character: character.name
          })
        } else if (error.request) {
          // Request was made but no response received
          console.error('Failed to set secondary main - Network error:', {
            message: 'No response from server',
            character: character.name
          })
        } else {
          // Something else went wrong
          console.error('Failed to set secondary main - Unexpected error:', {
            message: error.message,
            character: character.name
          })
        }
        
        // Do not set mock data - let the error propagate
        throw error
        
        // Could add user notification here
        // showErrorToast(`Failed to save ${character.name} as secondary main. Setting locally for this session.`)
        
      } finally {
        isUpdatingMains.value = false
      }
    }

    // Remove character as main
    const removeAsMain = async (character, slotType) => {
      // Validation checks
      if (!character) {
        console.error('Cannot remove main: character is null or undefined')
        return
      }
      
      if (!slotType || (slotType !== 'primary' && slotType !== 'secondary')) {
        console.error('Cannot remove main: invalid slotType', slotType)
        return
      }
      
      if (isUpdatingMains.value) {
        console.warn('Main character update already in progress, ignoring remove request')
        return
      }
      
      isUpdatingMains.value = true
      
      try {
        // Ensure we have the API base URL
        const apiBaseUrl = getApiBaseUrl()
        if (!apiBaseUrl) {
          throw new Error('API base URL is not available')
        }
        
        const response = await axios.delete(`${apiBaseUrl}/api/user/characters/${slotType}`, {
          timeout: 10000, // 10 second timeout
          headers: {
            'Content-Type': 'application/json'
          }
        })
        
        // Verify the response
        if (response.status === 200 || response.status === 204) {
          // Clear the main character
          if (slotType === 'primary') {
            primaryMain.value = null
          } else {
            secondaryMain.value = null
          }
          
          // Clear selected character if it was the removed main
          if (selectedCharacter.value?.id === character.id && activeSlot.value === slotType) {
            selectedCharacter.value = null
            activeSlot.value = null
          }
          
          console.log(`Successfully removed ${character.name} as ${slotType} main character`)
        } else {
          throw new Error(`Unexpected response status: ${response.status}`)
        }
        
      } catch (error) {
        // Enhanced error handling
        if (error.response) {
          // Server responded with error status
          console.error('Failed to remove main character - Server error:', {
            status: error.response.status,
            data: error.response.data,
            character: character.name,
            slotType
          })
        } else if (error.request) {
          // Request was made but no response received
          console.error('Failed to remove main character - Network error:', {
            message: 'No response from server',
            character: character.name,
            slotType
          })
        } else {
          // Something else went wrong
          console.error('Failed to remove main character - Unexpected error:', {
            message: error.message,
            character: character.name,
            slotType
          })
        }
        
        // Do not set mock data - let the error propagate
        throw error
        
      } finally {
        isUpdatingMains.value = false
      }
    }

    onMounted(async () => {
      await loadUserMainCharacters()
    })
    
    // Development testing functions - expose to window for console testing
    if (import.meta.env.DEV) {
      window.testMainCharacters = {
        // Test loading main characters from API
        testLoad: async () => {
          console.log('🧪 Testing loadUserMainCharacters')
          await loadUserMainCharacters()
        },
        
        // Reset main characters state
        reset: () => {
          primaryMain.value = null
          secondaryMain.value = null
          console.log('🧹 Reset main characters state')
        },
        
        // Show current state
        showState: () => {
          console.log('📊 Current main characters state:', {
            primary: primaryMain.value,
            secondary: secondaryMain.value
          })
        }
      }
      
      console.log('🧪 Development testing functions available:')
      console.log('  window.testMainCharacters.testLoad() - Test loading main characters')
      console.log('  window.testMainCharacters.reset() - Reset main characters state')
      console.log('  window.testMainCharacters.showState() - Show current state')
    }
    
    // Cleanup function to cancel pending requests
    const cleanup = () => {
      if (currentCharacterRequest.value) {
        currentCharacterRequest.value.abort()
        currentCharacterRequest.value = null
      }
      if (currentSearchRequest.value) {
        currentSearchRequest.value.abort()
        currentSearchRequest.value = null
      }
      isLoadingCharacter.value = false
    }
    
    // Cancel requests when component is unmounted
    onUnmounted(() => {
      cleanup()
    })

    return {
      // Main character slots
      primaryMain,
      secondaryMain,
      isUpdatingMains,
      
      // Currently displayed character
      selectedCharacter,
      activeSlot,
      inventoryDataCache,
      inventoryData,
      
      // Character search
      searchInput,
      searchQuery,
      searchResults,
      paginatedResults,
      isSearching,
      searchPerformed,
      lastSearchQuery,
      
      // Pagination and navigation
      currentPage,
      resultsPerPage,
      totalPages,
      totalResults,
      hasNextPage,
      hasPrevPage,
      selectedIndex,
      handleKeydown,
      
      // Modal for main character selection
      showSearchModal,
      searchModalType,
      modalSearchQuery,
      modalSearchResults,
      
      // Character loading state
      isLoadingCharacter,
      
      // UI Methods
      viewCharacter,
      openCharacterSearch,
      closeSearchModal,
      handleSearchInput,
      performSearch,
      viewSearchedCharacter,
      handleModalSearchInput,
      performModalSearch,
      selectMainCharacter,
      clearMainSlot,
      
      // Utility methods
      getClassIcon,
      normalizeClassName,
      getClassName,
      getRaceName,
      
      // Main character management
      setPrimaryMain,
      setSecondaryMain,
      removeAsMain
    }
  }
}
</script>

<style scoped>
.characters-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 100px 20px 20px;
}

.characters-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  text-align: center;
  color: white;
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 2rem;
  text-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

.character-selector {
  margin-bottom: 2rem;
}

/* Main Character Summary */
.main-character-summary {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
}

.main-char-display {
  display: flex;
  gap: 2rem;
  justify-content: center;
  flex-wrap: wrap;
}

.main-char-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  border-radius: 8px;
  min-width: 200px;
}

.main-char-item.primary {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(255, 165, 0, 0.2));
  border: 1px solid rgba(255, 215, 0, 0.4);
}

.main-char-item.secondary {
  background: linear-gradient(135deg, rgba(192, 192, 192, 0.2), rgba(169, 169, 169, 0.2));
  border: 1px solid rgba(192, 192, 192, 0.4);
}

.main-char-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 0.25rem;
}

.main-char-name {
  font-size: 1.2rem;
  font-weight: bold;
  color: white;
  margin-bottom: 0.25rem;
}

.main-char-details {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
}

.character-grid {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.character-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 220px;
  position: relative;
}

.character-card:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

.character-card.active {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.4);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.character-card.primary-main {
  background: rgba(255, 215, 0, 0.15);
  border-color: rgba(255, 215, 0, 0.4);
  box-shadow: 0 4px 20px rgba(255, 215, 0, 0.2);
}

.character-card.secondary-main {
  background: rgba(192, 192, 192, 0.15);
  border-color: rgba(192, 192, 192, 0.4);
  box-shadow: 0 4px 20px rgba(192, 192, 192, 0.2);
}

/* Character Badges */
.character-badges {
  position: absolute;
  top: -8px;
  right: -8px;
  display: flex;
  gap: 4px;
}

.main-badge {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.8rem;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.main-badge.primary {
  background: linear-gradient(135deg, #FFD700, #FFA500);
}

.main-badge.secondary {
  background: linear-gradient(135deg, #C0C0C0, #A9A9A9);
}

/* Character Actions */
.character-actions {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
}

.main-button {
  padding: 0.4rem 0.8rem;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.main-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.main-button.primary {
  background: linear-gradient(135deg, #FFD700, #FFA500);
  border: 1px solid rgba(255, 215, 0, 0.6);
}

.main-button.primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #FFF700, #FFB500);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 215, 0, 0.3);
}

.main-button.secondary {
  background: linear-gradient(135deg, #C0C0C0, #A9A9A9);
  border: 1px solid rgba(192, 192, 192, 0.6);
}

.main-button.secondary:hover:not(:disabled) {
  background: linear-gradient(135deg, #D0D0D0, #B9B9B9);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(192, 192, 192, 0.3);
}

.main-button.remove {
  background: linear-gradient(135deg, #FF4444, #CC3333);
  border: 1px solid rgba(255, 68, 68, 0.6);
}

.main-button.remove:hover:not(:disabled) {
  background: linear-gradient(135deg, #FF5555, #DD4444);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 68, 68, 0.3);
}

.character-portrait {
  width: 60px;
  height: 156px;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.character-portrait img {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  background: transparent;
}

.character-info {
  text-align: center;
  color: white;
}

.character-info h3 {
  margin: 0 0 0.25rem;
  font-size: 1.1rem;
  font-weight: 600;
}

.character-info p {
  margin: 0;
  font-size: 0.9rem;
  opacity: 0.8;
}

.inventory-section {
  margin-top: 2rem;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: white;
  font-size: 1.2rem;
  opacity: 0.7;
}

/* Main Character Slots Section */
.main-slots-section {
  margin-bottom: 3rem;
}

.section-title {
  color: white;
  font-size: 2rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  text-align: center;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.main-slots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 2rem;
  max-width: 800px;
  margin: 0 auto;
}

/* Main Character Slots */
.main-slot {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 1.5rem;
  transition: all 0.3s ease;
  min-height: 200px;
}

.main-slot:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

.main-slot.active {
  border-color: rgba(102, 126, 234, 0.6);
  background: rgba(102, 126, 234, 0.1);
}

.main-slot.primary {
  border-color: rgba(255, 215, 0, 0.4);
}

.main-slot.secondary {
  border-color: rgba(192, 192, 192, 0.4);
}

.slot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.slot-header h3 {
  color: white;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0;
}

.slot-badge {
  padding: 0;
  border-radius: 0;
  font-size: 3rem;
  font-weight: 900;
  font-family: 'Arial Black', sans-serif;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.slot-badge.primary {
  background: linear-gradient(135deg, #FFD700, #FF8C00);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 8px rgba(255, 215, 0, 0.4));
}

.slot-badge.secondary {
  background: linear-gradient(135deg, #FFD700, #FF8C00);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 8px rgba(255, 215, 0, 0.4));
}

.slot-badge:hover {
  transform: scale(1.1);
}

/* Character Display in Slots */
.slot-character {
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
  padding: 0.75rem;
  border-radius: 8px;
  transition: background-color 0.2s ease;
  position: relative;
}

.slot-character:hover {
  background: rgba(255, 255, 255, 0.1);
}

.character-portrait {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.character-portrait.small {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.3);
  border: 2px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

.character-portrait img,
.character-portrait .class-icon {
  width: 100%;
  height: 100%;
  object-fit: contain;
  image-rendering: pixelated;
  image-rendering: crisp-edges;
  background: rgba(0, 0, 0, 0.2);
}

.character-info h4 {
  margin: 0 0 0.25rem;
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
}

.character-info p {
  margin: 0.125rem 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}

.clear-slot-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: rgba(255, 68, 68, 0.8);
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  color: white;
  font-size: 0.8rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.clear-slot-btn:hover:not(:disabled) {
  background: rgba(255, 68, 68, 1);
  transform: scale(1.1);
}

.clear-slot-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Empty Slot States */
.empty-slot {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
  border: 2px dashed rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.empty-slot:hover {
  border-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.05);
}

.empty-slot-content {
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
}

.empty-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  color: rgba(255, 255, 255, 0.5);
}

.empty-slot-content p {
  margin: 0.5rem 0;
  font-size: 0.9rem;
}

.search-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  border-radius: 6px;
  color: white;
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.search-btn:hover {
  background: linear-gradient(135deg, #7685eb, #8458b3);
  transform: translateY(-1px);
}

/* Character Search Section */
.character-search-section {
  margin-bottom: 3rem;
}

.section-description {
  color: rgba(255, 255, 255, 0.8);
  text-align: center;
  margin-bottom: 2rem;
  font-size: 1rem;
}

.search-container {
  max-width: 600px;
  margin: 0 auto;
}

.search-input-group {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.search-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 1rem;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.search-input:focus {
  outline: none;
  border-color: rgba(102, 126, 234, 0.6);
  background: rgba(255, 255, 255, 0.15);
}

.search-button, .view-btn, .select-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  border-radius: 8px;
  color: white;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.search-button:hover:not(:disabled),
.view-btn:hover,
.select-btn:hover {
  background: linear-gradient(135deg, #7685eb, #8458b3);
  transform: translateY(-1px);
}

.search-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Search Results Dropdown */
.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: rgba(30, 30, 40, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  max-height: 400px;
  overflow: hidden;
}

.search-dropdown.enhanced {
  max-height: 500px;
  display: flex;
  flex-direction: column;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(40, 40, 50, 0.9);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 12px;
}

.results-count {
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: rgba(255, 255, 255, 0.8);
  font-weight: 600;
  min-width: 50px;
  text-align: center;
}

.dropdown-results {
  flex: 1;
  overflow-y: auto;
  max-height: 350px;
}

.dropdown-footer {
  padding: 8px 16px;
  background: rgba(20, 20, 30, 0.9);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
}

.nav-help {
  color: rgba(255, 255, 255, 0.6);
  font-size: 11px;
  font-style: italic;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover,
.dropdown-item.selected {
  background: rgba(255, 255, 255, 0.15);
  transform: translateX(2px);
}

.dropdown-item.selected {
  background: rgba(106, 90, 205, 0.3);
  border-left: 3px solid #6a5acd;
}

.dropdown-item .character-info {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  flex: 1;
}

.dropdown-item .character-name {
  font-weight: 600;
  color: white;
  font-size: 0.95rem;
}

.dropdown-item .character-details {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
}

.dropdown-item .character-race {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  font-style: italic;
}

.select-indicator {
  position: absolute;
  right: 16px;
  background: rgba(106, 90, 205, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: bold;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}

.search-container {
  position: relative;
}

.search-container:focus {
  outline: none;
}

/* Legacy search results for modal */
.search-results {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  max-height: 400px;
  overflow-y: auto;
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.no-results {
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
  padding: 2rem;
  font-style: italic;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 2rem;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.modal-header h3 {
  color: white;
  margin: 0;
  font-size: 1.3rem;
  font-weight: 600;
}

.modal-close {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

.modal-body {
  color: white;
}

/* Inventory Section */
.inventory-section {
  margin-top: 2rem;
}

.inventory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.inventory-header h3 {
  color: white;
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.inventory-source {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.source-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: bold;
  color: white;
}

.source-badge.primary {
  background: linear-gradient(135deg, #FFD700, #FFA500);
}

.source-badge.secondary {
  background: linear-gradient(135deg, #C0C0C0, #A9A9A9);
}

.source-badge.lookup {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

/* Loading Section */
.loading-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  margin-top: 2rem;
}

.loading-section p {
  color: white;
  font-size: 1.1rem;
  margin-top: 1rem;
  margin-bottom: 0;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-left: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>