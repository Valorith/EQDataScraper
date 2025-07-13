import { defineStore } from 'pinia'
import axios from 'axios'
import { API_BASE_URL, buildApiUrl, API_ENDPOINTS } from '@/config/api'

// Global debugging for network requests
const DEBUG_NETWORK = import.meta.env.MODE === 'development' && localStorage.getItem('debug-network') === 'true'

// Network request logger
function logNetworkRequest(method, url, data = null) {
  if (DEBUG_NETWORK) {
    console.log(`🌐 [${method.toUpperCase()}] ${url}`)
    if (data) {
      console.log('📤 Request data:', data)
    }
    console.log('📍 Full URL breakdown:', {
      API_BASE_URL,
      endpoint: url.replace(API_BASE_URL, ''),
      fullUrl: url,
      timestamp: new Date().toISOString()
    })
  }
}

function logNetworkResponse(method, url, response, duration) {
  if (DEBUG_NETWORK) {
    console.log(`📥 [${method.toUpperCase()}] ${url} - ${response.status} (${duration}ms)`)
    console.log('📤 Response headers:', response.headers)
    if (response.data) {
      const preview = typeof response.data === 'string' 
        ? response.data.substring(0, 200) + '...'
        : JSON.stringify(response.data).substring(0, 200) + '...'
      console.log('📤 Response preview:', preview)
    }
  }
}

function logNetworkError(method, url, error, duration) {
  if (DEBUG_NETWORK) {
    console.error(`💥 [${method.toUpperCase()}] ${url} - FAILED (${duration}ms)`)
    console.error('💥 Error details:', {
      message: error.message,
      code: error.code,
      status: error.response?.status,
      statusText: error.response?.statusText,
      responseData: error.response?.data,
      responseHeaders: error.response?.headers
    })
  }
}

export const useSpellsStore = defineStore('spells', {
  state: () => ({
    // Track active requests to prevent duplicate API calls
    activeRequests: new Map(),
    classes: [
      { name: 'Warrior', id: 1, color: '#8e2d2d', colorRgb: '142, 45, 45' },
      { name: 'Cleric', id: 2, color: '#ccccff', colorRgb: '204, 204, 255' },
      { name: 'Paladin', id: 3, color: '#ffd700', colorRgb: '255, 215, 0' },
      { name: 'Ranger', id: 4, color: '#228b22', colorRgb: '34, 139, 34' },
      { name: 'ShadowKnight', id: 5, color: '#551a8b', colorRgb: '85, 26, 139' },
      { name: 'Druid', id: 6, color: '#a0522d', colorRgb: '160, 82, 45' },
      { name: 'Monk', id: 7, color: '#556b2f', colorRgb: '85, 107, 47' },
      { name: 'Bard', id: 8, color: '#ff69b4', colorRgb: '255, 105, 180' },
      { name: 'Rogue', id: 9, color: '#708090', colorRgb: '112, 128, 144' },
      { name: 'Shaman', id: 10, color: '#20b2aa', colorRgb: '32, 178, 170' },
      { name: 'Necromancer', id: 11, color: '#4b0082', colorRgb: '75, 0, 130' },
      { name: 'Wizard', id: 12, color: '#1e90ff', colorRgb: '30, 144, 255' },
      { name: 'Magician', id: 13, color: '#ff8c00', colorRgb: '255, 140, 0' },
      { name: 'Enchanter', id: 14, color: '#9370db', colorRgb: '147, 112, 219' },
      { name: 'Beastlord', id: 15, color: '#a52a2a', colorRgb: '165, 42, 42' },
      { name: 'Berserker', id: 16, color: '#b22222', colorRgb: '178, 34, 34' }
    ],
    spellsData: {},
    spellsMetadata: {}, // Store cache metadata (timestamps, expiry status)
    loading: false,
    error: null
  }),

  getters: {
    getClassByName: (state) => (className) => {
      return state.classes.find(cls => cls.name.toLowerCase() === className.toLowerCase())
    },
    
    getSpellsForClass: (state) => (className) => {
      // Always normalize to lowercase for consistent lookups
      const normalizedClassName = className.toLowerCase()
      return state.spellsData[normalizedClassName] || []
    },

    getSpellsMetadata: (state) => (className) => {
      // Get cache metadata (timestamps, expiry status) for a class
      const normalizedClassName = className.toLowerCase()
      return state.spellsMetadata[normalizedClassName] || null
    },

    isClassHydrated: (state) => (className) => {
      // Check if a class has been hydrated (loaded into memory)
      const normalizedClassName = className.toLowerCase()
      return state.spellsData[normalizedClassName] && state.spellsData[normalizedClassName].length > 0
    },

    getHydratedClasses: (state) => {
      // Get list of all classes that have been hydrated into memory
      return Object.keys(state.spellsData).filter(className => 
        state.spellsData[className] && state.spellsData[className].length > 0
      )
    }
  },

  actions: {
    // Warmup the backend connection with a single attempt
    async warmupBackend() {
      // Skip backend check entirely in offline mode
      if (import.meta.env.VITE_OFFLINE_MODE === 'true') {
        sessionStorage.setItem('backend_available', 'false')
        return false
      }
      
      const startTime = Date.now()
      const healthUrl = buildApiUrl(API_ENDPOINTS.HEALTH)
      
      try {
        const response = await axios.get(healthUrl, { 
          timeout: 5000,
          headers: { 'Accept': 'application/json' }
        })
        
        const duration = Date.now() - startTime
        console.log(`✅ Backend responded in ${duration}ms`)
        sessionStorage.setItem('backend_available', 'true')
        return true
      } catch (error) {
        // Mark backend as unavailable to prevent further checks
        if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
          sessionStorage.setItem('backend_available', 'false')
        }
        
        // Silently handle expected errors during startup
        if (error.response?.status !== 429 && 
            error.code !== 'ERR_NETWORK' && 
            error.code !== 'ECONNREFUSED') {
          // Only log unexpected errors
          console.warn('Backend warmup failed:', error.message)
        }
        return false
      }
    },

    // Spell system disabled - cache status check disabled
    async checkCacheStatus() {
      console.warn('Cache status check disabled - spell system temporarily disabled')
      return { disabled: true, message: 'Spell system temporarily disabled for redesign' }
    },

    // Force refresh: clear memory and update cache DB
    async forceRefreshAllData() {
      try {
        console.log('🔄 Force refresh initiated: clearing memory and updating cache database...')
        
        // Clear all memory data
        this.spellsData = {}
        this.spellsMetadata = {}
        
        // Force update the cache database
        console.log('📋 Forcing cache database update...')
        await axios.post(`${API_BASE_URL}/api/scrape-all`, {}, {
          timeout: 300000, // 5 minutes for full refresh
          headers: { 'Accept': 'application/json' }
        })
        
        console.log('✅ Cache database updated successfully')
        return true
        
      } catch (error) {
        console.error('❌ Force refresh failed:', error.message)
        throw error
      }
    },

    // Spell system disabled - fetch functionality disabled
    async fetchSpellsForClass(className, forceRefresh = false) {
      console.warn('Spell fetching disabled - spell system temporarily disabled')
      this.error = 'Spell system temporarily disabled for redesign'
      throw new Error('Spell system temporarily disabled for redesign')
    },

    async _fetchSpellsInternal(normalizedClassName, forceRefresh) {
      const startTime = Date.now()
      const apiUrl = `${API_BASE_URL}/api/spells/${normalizedClassName}`
      
      try {
        logNetworkRequest('GET', apiUrl)
        
        // Check if server has data preloaded for faster timeout
        const isServerOptimized = this.spellsData[normalizedClassName] && 
          this.spellsData[normalizedClassName][0]._serverOptimized
        
        // Use shorter timeout when server has data preloaded, longer for fresh scraping
        const response = await axios.get(apiUrl, {
          timeout: isServerOptimized ? 10000 : 60000, // 10s for server memory, 60s for fresh scraping
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          // Add connection pooling settings for better reliability
          maxRedirects: 3,
          validateStatus: (status) => status >= 200 && status < 300
        })
        
        const duration = Date.now() - startTime
        logNetworkResponse('GET', apiUrl, response, duration)
        
        // Handle the new API response format
        const spellsData = response.data.spells || response.data
        
        if (!Array.isArray(spellsData)) {
          throw new Error('Invalid response format from server')
        }
        
        // Store metadata (timestamps, cache status)
        this.spellsMetadata[normalizedClassName] = {
          last_updated: response.data.last_updated || new Date().toISOString(),
          cached: response.data.cached || false,
          expired: response.data.expired || false,
          spell_count: response.data.spell_count || spellsData.length,
          stale: response.data.stale || false
        }
        
        // Check for stale cache warning
        if (response.data.stale && response.data.message) {
          console.warn(`Stale data warning: ${response.data.message}`)
          // Could show a toast notification here if needed
        }
        
        this.spellsData[normalizedClassName] = spellsData
        return spellsData
      } catch (error) {
        const duration = Date.now() - startTime
        logNetworkError('GET', apiUrl, error, duration)
        
        let errorMessage = 'An unexpected error occurred'
        
        if (error.response) {
          // Server responded with error status
          switch (error.response.status) {
            case 404:
              errorMessage = `No spells found for ${className}. Try scraping data first.`
              break
            case 429:
              // Rate limited
              const retryAfter = error.response.data?.retry_after_minutes || 5
              errorMessage = `Rate limited. Please wait ${retryAfter.toFixed(1)} minutes before trying again.`
              break
            case 500:
              errorMessage = 'Server error. Please try again later.'
              break
            case 503:
              errorMessage = 'Service temporarily unavailable. Check your connection.'
              break
            default:
              errorMessage = error.response.data?.error || `Server error (${error.response.status})`
          }
        } else if (error.request) {
          // Network error
          errorMessage = 'Unable to connect to server. Please check your connection.'
        } else if (error.code === 'ECONNABORTED') {
          // Timeout
          errorMessage = 'Request timed out. The server may be busy.'
        } else {
          errorMessage = error.message || 'An unexpected error occurred'
        }
        
        this.error = errorMessage
        console.error('Error fetching spells:', error)
        throw new Error(errorMessage)
      } finally {
        this.loading = false
      }
    },

    // DISABLED: Spell system temporarily disabled for redesign
    async scrapeAllClasses() {
      console.warn('Scraping disabled - spell system temporarily disabled')
      this.error = 'Spell system temporarily disabled for redesign'
      throw new Error('Spell system temporarily disabled for redesign')
    },

    // DISABLED: Spell system temporarily disabled for redesign
    async scrapeSpecificClass(className) {
      console.warn('Scraping disabled - spell system temporarily disabled')
      this.error = 'Spell system temporarily disabled for redesign'
      throw new Error('Spell system temporarily disabled for redesign')
    }
  }
}) 