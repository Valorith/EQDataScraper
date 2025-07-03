import { defineStore } from 'pinia'
import axios from 'axios'

// Configure API base URL - use environment variable in production, direct connection in development
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 
  (import.meta.env.PROD ? 'https://eqdatascraper-backend-production.up.railway.app' : 'http://localhost:5001')

export const useSpellsStore = defineStore('spells', {
  state: () => ({
    // Track active requests to prevent duplicate API calls
    activeRequests: new Map(),
    // Cache pre-hydration status
    isPreHydrating: false,
    preHydrationProgress: { loaded: 0, total: 0 },
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
    // Warmup the backend connection with resilient retry strategy
    async warmupBackend() {
      const maxRetries = 3
      const timeouts = [10000, 20000, 30000] // Progressive timeouts for Railway cold starts
      
      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
          console.log(`🔗 Backend warmup attempt ${attempt}/${maxRetries} (${timeouts[attempt-1]/1000}s timeout)...`)
          
          await axios.get(`${API_BASE_URL}/api/health`, { 
            timeout: timeouts[attempt - 1],
            headers: { 'Accept': 'application/json' }
          })
          
          console.log(`✅ Backend warmup successful on attempt ${attempt}`)
          return true
        } catch (error) {
          console.warn(`⚠️ Backend warmup attempt ${attempt} failed:`, error.message)
          
          if (attempt === maxRetries) {
            console.error('❌ All backend warmup attempts failed. App will function with on-demand loading.')
            return false
          }
          
          // Brief delay before retry (Railway container might be starting)
          await new Promise(resolve => setTimeout(resolve, 2000))
        }
      }
      
      return false
    },

    // Two-phase cache system: update cache DB, then hydrate memory for instant access
    async preHydrateCache() {
      try {
        this.isPreHydrating = true
        console.log('🚀 Starting intelligent cache pre-hydration...')
        
        // First check if server has already preloaded data on startup
        console.log('🔍 Checking server memory status...')
        const healthCheck = await axios.get(`${API_BASE_URL}/api/health`, {
          timeout: 5000,
          headers: { 'Accept': 'application/json' }
        })
        
        if (healthCheck.data.ready_for_instant_responses && healthCheck.data.startup_complete) {
          console.log('✅ Server already has spell data preloaded in memory!')
          console.log('⚡ Loading class metadata for instant UI updates...')
          
          // Load minimal dataset to populate local store for UI state consistency
          // This ensures class cards show as "hydrated" while maintaining server optimization
          const cacheStatus = await axios.get(`${API_BASE_URL}/api/cache-status`, {
            timeout: 5000,
            headers: { 'Accept': 'application/json' }
          })
          
          const classesToHydrate = Object.keys(cacheStatus.data)
            .filter(key => key !== '_config' && cacheStatus.data[key].cached === true)
            .slice(0, 3) // Load just 3 classes for UI state consistency
            .map(cls => cls.toLowerCase())
          
          console.log(`🎯 Loading metadata for ${classesToHydrate.length} classes to update UI state:`, classesToHydrate)
          
          for (const className of classesToHydrate) {
            try {
              await this.fetchSpellsForClass(className)
              console.log(`✅ Loaded metadata for ${className}`)
            } catch (error) {
              console.warn(`⚠️ Failed to load metadata for ${className}:`, error.message)
            }
          }
          
          this.isPreHydrating = false
          console.log('🎉 Server optimization + UI state loading complete!')
          return true
        }
        
        // If server memory not ready, proceed with pre-hydration
        console.log('📋 Server memory not fully loaded, proceeding with cache pre-hydration...')
        
        // Phase 1: Validate and update cache database (single source of truth)
        const cacheStatus = await axios.get(`${API_BASE_URL}/api/cache-status`, {
          timeout: 5000,
          headers: { 'Accept': 'application/json' }
        })
        
        const allClasses = Object.keys(cacheStatus.data).filter(key => key !== '_config')
        const cachedClasses = allClasses.filter(cls => cacheStatus.data[cls].cached === true)
        const uncachedClasses = allClasses.filter(cls => cacheStatus.data[cls].cached === false)
        
        console.log(`📊 Cache DB Status: ${cachedClasses.length} cached, ${uncachedClasses.length} uncached`)
        
        // If there are uncached classes, update the cache database first
        if (uncachedClasses.length > 0) {
          console.log(`🔄 Updating cache database for ${uncachedClasses.length} uncached classes...`)
          try {
            await axios.post(`${API_BASE_URL}/api/scrape-all`, {}, {
              timeout: 180000, // 3 minutes for cache updates
              headers: { 'Accept': 'application/json' }
            })
            console.log('✅ Cache database updated successfully')
            
            // Re-check cache status after update
            const updatedStatus = await axios.get(`${API_BASE_URL}/api/cache-status`, {
              timeout: 5000,
              headers: { 'Accept': 'application/json' }
            })
            const updatedCachedClasses = Object.keys(updatedStatus.data)
              .filter(key => key !== '_config' && updatedStatus.data[key].cached === true)
            console.log(`📊 Updated cache: ${updatedCachedClasses.length} classes now cached in database`)
          } catch (cacheUpdateError) {
            console.warn('⚠️ Cache database update failed, proceeding with existing cache:', cacheUpdateError.message)
          }
        }
        
        // Phase 2: Load cached data from DB into memory for instant access
        console.log('💾 Phase 2: Loading validated cache data into memory for instant access...')
        
        // Get final cache status for memory hydration
        const finalCacheStatus = await axios.get(`${API_BASE_URL}/api/cache-status`, {
          timeout: 5000,
          headers: { 'Accept': 'application/json' }
        })
        
        const classesToHydrate = Object.keys(finalCacheStatus.data)
          .filter(key => key !== '_config' && finalCacheStatus.data[key].cached === true)
          .map(cls => cls.toLowerCase())
        
        console.log(`🎯 Hydrating ${classesToHydrate.length} cached classes into memory:`, classesToHydrate)
        
        this.preHydrationProgress = { loaded: 0, total: classesToHydrate.length }
        
        // Load classes in parallel with concurrency limit
        const batchSize = 4 // Load 4 classes at a time for comprehensive caching
        for (let i = 0; i < classesToHydrate.length; i += batchSize) {
          const batch = classesToHydrate.slice(i, i + batchSize)
          
          await Promise.all(batch.map(async (className) => {
            try {
              await this.fetchSpellsForClass(className)
              this.preHydrationProgress.loaded++
              console.log(`✅ Pre-loaded ${className} (${this.preHydrationProgress.loaded}/${this.preHydrationProgress.total})`)
            } catch (error) {
              this.preHydrationProgress.loaded++
              console.warn(`⚠️ Failed to pre-load ${className}:`, error.message)
            }
          }))
          
          // Small delay between batches to be backend-friendly
          if (i + batchSize < classesToHydrate.length) {
            await new Promise(resolve => setTimeout(resolve, 500))
          }
        }
        
        console.log(`🎉 Two-phase cache system complete! Database validated → ${Object.keys(this.spellsData).length} classes hydrated into memory for instant navigation`)
        return true
        
      } catch (error) {
        console.warn('Cache pre-hydration failed:', error.message)
        return false
      } finally {
        this.isPreHydrating = false
      }
    },

    // Force refresh: clear memory, update cache DB, then re-hydrate
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
        
        console.log('✅ Cache database updated, starting memory re-hydration...')
        
        // Re-hydrate memory with fresh data
        await this.preHydrateCache()
        
        console.log('🎉 Force refresh complete: cache updated and memory re-hydrated')
        return true
        
      } catch (error) {
        console.error('❌ Force refresh failed:', error.message)
        throw error
      }
    },

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
        console.log(`⚡ Instant memory cache hit for ${normalizedClassName}: ${this.spellsData[normalizedClassName].length} spells`)
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
        const apiUrl = `${API_BASE_URL}/api/spells/${normalizedClassName}`
        console.log('API_BASE_URL:', API_BASE_URL)
        console.log('Making API call to:', apiUrl)
        
        // Use optimized single request with longer initial timeout to avoid failed first attempts
        const response = await axios.get(apiUrl, {
          timeout: 60000, // 60 second timeout to handle both cached and fresh scraping
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          // Add connection pooling settings for better reliability
          maxRedirects: 3,
          validateStatus: (status) => status >= 200 && status < 300
        })
        
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