import { defineStore } from 'pinia'
import axios from 'axios'

// Configure API base URL - use environment variable if explicitly set, otherwise use appropriate defaults
const API_BASE_URL = (() => {
  // In production, only use VITE_BACKEND_URL if it's a valid production URL
  if (import.meta.env.PROD) {
    const envUrl = import.meta.env.VITE_BACKEND_URL
    // Only use env URL if it's a valid production URL (not localhost)
    if (envUrl && !envUrl.includes('localhost') && !envUrl.includes('127.0.0.1')) {
      console.log('🔧 Using environment variable VITE_BACKEND_URL:', envUrl)
      return envUrl
    }
    // Default production backend URL
    const defaultUrl = 'https://eqdatascraper-backend-production.up.railway.app'
    console.log('🔧 Using default production backend URL:', defaultUrl)
    return defaultUrl
  }
  
  // In development, use env variable or default to localhost
  const devUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5005'
  console.log('🔧 Using development backend URL:', devUrl)
  return devUrl
})()

// Global debugging for network requests
const DEBUG_NETWORK = import.meta.env.PROD || localStorage.getItem('debug-network') === 'true'

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
        const startTime = Date.now()
        const healthUrl = `${API_BASE_URL}/api/health`
        
        try {
          console.log(`🔗 Backend warmup attempt ${attempt}/${maxRetries} (${timeouts[attempt-1]/1000}s timeout)...`)
          logNetworkRequest('GET', healthUrl)
          
          const response = await axios.get(healthUrl, { 
            timeout: timeouts[attempt - 1],
            headers: { 'Accept': 'application/json' }
          })
          
          const duration = Date.now() - startTime
          logNetworkResponse('GET', healthUrl, response, duration)
          console.log(`✅ Backend warmup successful on attempt ${attempt}`)
          return true
        } catch (error) {
          const duration = Date.now() - startTime
          logNetworkError('GET', healthUrl, error, duration)
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
        const healthUrl = `${API_BASE_URL}/api/health`
        const startTime = Date.now()
        logNetworkRequest('GET', healthUrl)
        
        const healthCheck = await axios.get(healthUrl, {
          timeout: 5000,
          headers: { 'Accept': 'application/json' }
        })
        
        const duration = Date.now() - startTime
        logNetworkResponse('GET', healthUrl, healthCheck, duration)
        
        if (healthCheck.data.ready_for_instant_responses) {
          console.log('✅ Server already has spell data preloaded in memory!')
          console.log('⚡ Marking all cached classes as hydrated for instant UI updates...')
          
          // Get cache status to identify all cached classes
          const cacheStatus = await axios.get(`${API_BASE_URL}/api/cache-status`, {
            timeout: 5000,
            headers: { 'Accept': 'application/json' }
          })
          
          const cachedClasses = Object.keys(cacheStatus.data)
            .filter(key => key !== '_config' && cacheStatus.data[key].cached === true)
          
          console.log(`🎯 Marking ${cachedClasses.length} cached classes as hydrated:`, cachedClasses)
          
          // Mark all cached classes as hydrated with lightweight placeholder data
          // This updates UI state without heavy data loading since server has everything ready
          for (const className of cachedClasses) {
            const normalizedClassName = className.toLowerCase()
            
            // Create lightweight placeholder that marks the class as "hydrated" for UI
            // Real data will be loaded instantly from server memory when class is accessed
            this.spellsData[normalizedClassName] = [{
              _placeholder: true,
              _serverReady: true,
              _serverOptimized: true,
              name: `${className} spells ready on server`,
              level: 0
            }]
            
            // Store cache metadata
            this.spellsMetadata[normalizedClassName] = {
              last_updated: cacheStatus.data[className].last_updated,
              cached: true,
              expired: false,
              spell_count: cacheStatus.data[className].spell_count,
              stale: false,
              _serverOptimized: true
            }
          }
          
          this.isPreHydrating = false
          console.log(`🎉 Server optimization complete! All ${cachedClasses.length} classes marked as ready for instant loading`)
          return true
        }
        
        // If server memory not ready, proceed with simplified pre-hydration
        console.log('📋 Server memory not fully loaded, proceeding with simplified cache pre-hydration...')
        
        // Since server handles cache refresh on startup, we just need to trigger a refresh
        // The server will handle cache database updates and memory loading
        console.log('🔄 Triggering server-side cache refresh...')
        try {
          await axios.post(`${API_BASE_URL}/api/scrape-all`, {}, {
            timeout: 180000, // 3 minutes for cache updates
            headers: { 'Accept': 'application/json' }
          })
          console.log('✅ Server-side cache refresh completed')
          
          // Re-check server memory status after refresh
          const refreshedHealthCheck = await axios.get(`${API_BASE_URL}/api/health`, {
            timeout: 5000,
            headers: { 'Accept': 'application/json' }
          })
          
          if (refreshedHealthCheck.data.ready_for_instant_responses) {
            console.log('🎯 Server memory now ready - marking all classes as ready for instant loading')
            
            // Get cache status to identify all cached classes
            const cacheStatus = await axios.get(`${API_BASE_URL}/api/cache-status`, {
              timeout: 5000,
              headers: { 'Accept': 'application/json' }
            })
            
            const cachedClasses = Object.keys(cacheStatus.data)
              .filter(key => key !== '_config' && cacheStatus.data[key].cached === true)
            
            // Mark all cached classes as ready with lightweight placeholders
            for (const className of cachedClasses) {
              const normalizedClassName = className.toLowerCase()
              
              this.spellsData[normalizedClassName] = [{
                _placeholder: true,
                _serverReady: true,
                _serverOptimized: true,
                name: `${className} spells ready on server`,
                level: 0
              }]
              
              this.spellsMetadata[normalizedClassName] = {
                last_updated: cacheStatus.data[className].last_updated,
                cached: true,
                expired: false,
                spell_count: cacheStatus.data[className].spell_count,
                stale: false,
                _serverOptimized: true
              }
            }
            
            console.log(`🎉 Simplified cache system complete! All ${cachedClasses.length} classes ready for instant loading`)
          } else {
            console.log('⚠️ Server memory not ready after refresh - using fallback loading')
          }
          
        } catch (cacheUpdateError) {
          console.warn('⚠️ Server-side cache refresh failed:', cacheUpdateError.message)
        }
        
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
        // Check if this is placeholder data from server optimization
        if (this.spellsData[normalizedClassName][0]._placeholder && this.spellsData[normalizedClassName][0]._serverReady) {
          console.log(`⚡ Server has ${normalizedClassName} preloaded - fetching real data instantly`)
          // Continue to fetch real data from server memory (should be instant)
        } else {
          console.log(`⚡ Instant memory cache hit for ${normalizedClassName}: ${this.spellsData[normalizedClassName].length} spells`)
          return this.spellsData[normalizedClassName]
        }
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
      const startTime = Date.now()
      const apiUrl = `${API_BASE_URL}/api/spells/${normalizedClassName}`
      
      try {
        console.log('API_BASE_URL:', API_BASE_URL)
        console.log('Making API call to:', apiUrl)
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