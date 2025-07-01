import { defineStore } from 'pinia'
import axios from 'axios'

// Configure API base URL - use environment variable in production, relative path in development
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 
  (import.meta.env.PROD ? 'https://eqdatascraper-backend-production.up.railway.app' : '')

export const useSpellsStore = defineStore('spells', {
  state: () => ({
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
    }
  },

  actions: {
    async fetchSpellsForClass(className) {
      // Normalize the className to lowercase for consistent caching
      const normalizedClassName = className.toLowerCase()
      
      // Check for cached data first
      if (this.spellsData[normalizedClassName] && this.spellsData[normalizedClassName].length > 0) {
        return this.spellsData[normalizedClassName]
      }

      this.loading = true
      this.error = null

      try {
        const apiUrl = `${API_BASE_URL}/api/spells/${className}`
        console.log('API_BASE_URL:', API_BASE_URL)
        console.log('Making API call to:', apiUrl)
        
        const response = await axios.get(apiUrl, {
          timeout: 30000, // 30 second timeout
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        })
        
        // Handle the new API response format
        const spellsData = response.data.spells || response.data
        
        if (!Array.isArray(spellsData)) {
          throw new Error('Invalid response format from server')
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
    }
  }
}) 