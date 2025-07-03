import { defineStore } from 'pinia'
import axios from 'axios'

// Configure API base URL - use environment variable in production, proxy in development
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 
  (import.meta.env.PROD ? 'https://eqdatascraper-backend-production.up.railway.app' : '')

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
    }
  },

  actions: {
    async fetchSpellsForClass(className, forceRefresh = false) {
      // Normalize the className to lowercase for consistent caching
      const normalizedClassName = className.toLowerCase()
      const requestKey = `${normalizedClassName}-${forceRefresh}`
      
      // Return existing promise if request is already in flight
      if (this.activeRequests.has(requestKey)) {
        console.log(`Returning existing request for ${requestKey}`)
        return this.activeRequests.get(requestKey)
      }
      
      // Check for cached data first (skip if forcing refresh)
      if (!forceRefresh && this.spellsData[normalizedClassName] && this.spellsData[normalizedClassName].length > 0) {
        return this.spellsData[normalizedClassName]
      }

      this.loading = true
      this.error = null
      
      // Create and cache the request promise
      const requestPromise = this._fetchSpellsInternal(normalizedClassName, forceRefresh)
      this.activeRequests.set(requestKey, requestPromise)
      
      try {
        const result = await requestPromise
        return result
      } finally {
        this.activeRequests.delete(requestKey)
      }
    },

    async _fetchSpellsInternal(normalizedClassName, forceRefresh) {
      try {
        // Quick backend readiness check for better first-load reliability
        try {
          await axios.get(`${API_BASE_URL}/api/health`, { timeout: 2000 })
        } catch (healthError) {
          console.warn('Backend health check failed, proceeding anyway:', healthError.message)
        }
        
        const apiUrl = `${API_BASE_URL}/api/spells/${normalizedClassName}`
        console.log('API_BASE_URL:', API_BASE_URL)
        console.log('Making API call to:', apiUrl)
        
        // Try with shorter timeout first, then fallback to longer timeout
        let response
        try {
          response = await axios.get(apiUrl, {
            timeout: 5000, // 5 second timeout for first attempt
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            }
          })
        } catch (firstError) {
          console.warn('First attempt failed, retrying with longer timeout:', firstError.message)
          
          // Add a small delay before retry to allow backend to stabilize
          await new Promise(resolve => setTimeout(resolve, 500))
          
          // Retry with longer timeout for cold cache scenarios
          response = await axios.get(apiUrl, {
            timeout: 45000, // 45 second timeout for retry (cold cache scraping)
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            }
          })
        }
        
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

    async scrapeAllClasses() {
      this.loading = true
      this.error = null

      try {
        const response = await axios.post(`${API_BASE_URL}/api/scrape-all`)
        return response.data
      } catch (error) {
        this.error = error.message
        console.error('Error scraping all classes:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async scrapeSpecificClass(className) {
      this.loading = true
      this.error = null

      try {
        const response = await axios.post(`${API_BASE_URL}/api/refresh-spell-cache/${className}`)
        return response.data
      } catch (error) {
        this.error = error.message
        console.error('Error scraping specific class:', error)
        throw error
      } finally {
        this.loading = false
      }
    }
  }
}) 