/**
 * Test suite for Pinia spells store
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSpellsStore } from '@/stores/spells'
import { mockAxiosResponse, mockSpellData, mockCacheStatus } from '../setup.js'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

describe('Spells Store', () => {
  let store
  let mockAxios

  beforeEach(async () => {
    setActivePinia(createPinia())
    store = useSpellsStore()
    mockAxios = await import('axios')
  })

  describe('State Management', () => {
    it('should initialize with correct default state', () => {
      expect(store.classes).toEqual([])
      expect(store.selectedClass).toBe('')
      expect(store.spells).toEqual([])
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.cacheStatus).toEqual({})
    })

    it('should handle loading state correctly', () => {
      store.setLoading(true)
      expect(store.loading).toBe(true)
      
      store.setLoading(false)
      expect(store.loading).toBe(false)
    })

    it('should handle error state correctly', () => {
      const errorMessage = 'Test error'
      store.setError(errorMessage)
      expect(store.error).toBe(errorMessage)
      
      store.setError(null)
      expect(store.error).toBeNull()
    })
  })

  describe('Class Management', () => {
    it('should fetch and store classes', async () => {
      const mockClasses = [
        { name: 'Cleric', id: '2', color: '#ffffff' },
        { name: 'Wizard', id: '14', color: '#4169e1' }
      ]

      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse(mockClasses))

      await store.fetchClasses()

      expect(store.classes).toEqual(mockClasses)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('should handle fetch classes error', async () => {
      mockAxios.default.get.mockRejectedValueOnce(new Error('Network error'))

      await store.fetchClasses()

      expect(store.error).toContain('Failed to load classes')
      expect(store.loading).toBe(false)
    })

    it('should set selected class', () => {
      store.setSelectedClass('cleric')
      expect(store.selectedClass).toBe('cleric')
    })
  })

  describe('Spell Management', () => {
    it('should fetch and store spells for a class', async () => {
      const mockResponse = {
        spells: mockSpellData,
        cached: true,
        last_updated: '2025-07-02T12:58:55.856237',
        spell_count: 2
      }

      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse(mockResponse))

      await store.fetchSpells('cleric')

      expect(store.spells).toEqual(mockSpellData)
      expect(store.selectedClass).toBe('cleric')
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('should handle fetch spells error', async () => {
      mockAxios.default.get.mockRejectedValueOnce(new Error('Server error'))

      await store.fetchSpells('cleric')

      expect(store.error).toContain('Failed to load spells')
      expect(store.loading).toBe(false)
    })

    it('should handle API returning HTML instead of JSON', async () => {
      const htmlResponse = '<!DOCTYPE html><html></html>'
      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse(htmlResponse))

      await store.fetchSpells('cleric')

      expect(store.error).toContain('API returned HTML instead of JSON')
    })
  })

  describe('Cache Status Management', () => {
    it('should fetch and store cache status', async () => {
      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse(mockCacheStatus))

      await store.fetchCacheStatus('cleric')

      expect(store.cacheStatus).toEqual(mockCacheStatus)
    })

    it('should handle cache status fetch error', async () => {
      mockAxios.default.get.mockRejectedValueOnce(new Error('Cache error'))

      await store.fetchCacheStatus('cleric')

      expect(store.error).toContain('Failed to load cache status')
    })
  })

  describe('Search Functionality', () => {
    it('should search spells across classes', async () => {
      const mockSearchResults = [
        {
          name: 'Courage',
          spell_id: '202',
          level: 1,
          classes: ['CLR'],
          icon: 'spell_202.png'
        }
      ]

      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse(mockSearchResults))

      const results = await store.searchSpells('courage')

      expect(results).toEqual(mockSearchResults)
    })

    it('should handle search error', async () => {
      mockAxios.default.get.mockRejectedValueOnce(new Error('Search error'))

      const results = await store.searchSpells('courage')

      expect(results).toEqual([])
      expect(store.error).toContain('Search failed')
    })

    it('should handle empty search query', async () => {
      const results = await store.searchSpells('')
      expect(results).toEqual([])
    })
  })

  describe('Computed Properties', () => {
    beforeEach(() => {
      store.spells = mockSpellData
    })

    it('should compute spell count correctly', () => {
      expect(store.spellCount).toBe(2)
    })

    it('should filter spells by level', () => {
      const level1Spells = store.getSpellsByLevel(1)
      expect(level1Spells).toHaveLength(2)
      expect(level1Spells.every(spell => spell.level === 1)).toBe(true)
    })

    it('should group spells by level', () => {
      const grouped = store.spellsByLevel
      expect(grouped).toHaveProperty('1')
      expect(grouped['1']).toHaveLength(2)
    })

    it('should compute pricing statistics', () => {
      const stats = store.pricingStats
      expect(stats.total).toBe(2)
      expect(stats.withPricing).toBe(2)
      expect(stats.successful).toBe(1) // Only one spell has actual pricing
      expect(stats.failed).toBe(1) // One spell has unknown: true
    })
  })

  describe('Data Validation', () => {
    it('should validate spell data structure', () => {
      store.spells = mockSpellData

      store.spells.forEach(spell => {
        expect(spell).toHaveProperty('name')
        expect(spell).toHaveProperty('level')
        expect(spell).toHaveProperty('spell_id')
        expect(spell).toHaveProperty('pricing')
        
        if (spell.pricing) {
          expect(spell.pricing).toHaveProperty('platinum')
          expect(spell.pricing).toHaveProperty('gold')
          expect(spell.pricing).toHaveProperty('silver')
          expect(spell.pricing).toHaveProperty('bronze')
        }
      })
    })

    it('should handle malformed spell data gracefully', () => {
      const malformedData = [
        { name: 'Incomplete Spell' }, // Missing required fields
        null,
        undefined
      ]

      expect(() => {
        store.spells = malformedData.filter(Boolean)
      }).not.toThrow()
    })
  })

  describe('Performance and Optimization', () => {
    it('should not refetch classes if already loaded', async () => {
      store.classes = [{ name: 'Cleric', id: '2' }]
      
      await store.fetchClasses()
      
      expect(mockAxios.default.get).not.toHaveBeenCalled()
    })

    it('should handle large spell datasets efficiently', () => {
      const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
        ...mockSpellData[0],
        spell_id: i.toString(),
        name: `Spell ${i}`
      }))

      const start = performance.now()
      store.spells = largeDataset
      const end = performance.now()

      expect(end - start).toBeLessThan(100) // Should complete in under 100ms
      expect(store.spellCount).toBe(1000)
    })
  })

  describe('Cache Pre-hydration and Server Optimization', () => {
    it('should handle server warmup with retry logic', async () => {
      // First attempt fails, second succeeds
      mockAxios.default.get.mockRejectedValueOnce(new Error('Connection failed'))
      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse({ status: 'healthy' }))

      const result = await store.warmupBackend()

      expect(result).toBe(true)
      expect(mockAxios.default.get).toHaveBeenCalledTimes(2)
      expect(mockAxios.default.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/health'),
        expect.objectContaining({ timeout: 10000 })
      )
    })

    it('should handle server warmup complete failure', async () => {
      // All attempts fail
      mockAxios.default.get.mockRejectedValue(new Error('Server down'))

      const result = await store.warmupBackend()

      expect(result).toBe(false)
      expect(mockAxios.default.get).toHaveBeenCalledTimes(3) // Max retries
    })

    it('should optimize cache when server is ready', async () => {
      // Mock server ready response
      const healthResponse = {
        ready_for_instant_responses: true,
        startup_complete: true
      }
      
      const cacheStatusResponse = {
        cleric: { cached: true, spell_count: 219, last_updated: '2025-07-03T10:00:00Z' },
        wizard: { cached: true, spell_count: 213, last_updated: '2025-07-03T10:00:00Z' },
        _config: { spell_cache_expiry_hours: 24 }
      }

      mockAxios.default.get
        .mockResolvedValueOnce(mockAxiosResponse(healthResponse))
        .mockResolvedValueOnce(mockAxiosResponse(cacheStatusResponse))

      const result = await store.preHydrateCache()

      expect(result).toBe(true)
      expect(store.isPreHydrating).toBe(false)
      
      // Should mark cached classes as hydrated with placeholders
      expect(store.isClassHydrated('cleric')).toBe(true)
      expect(store.isClassHydrated('wizard')).toBe(true)
      
      // Check placeholder structure
      const clericData = store.getSpellsForClass('cleric')
      expect(clericData[0]._placeholder).toBe(true)
      expect(clericData[0]._serverReady).toBe(true)
      expect(clericData[0]._serverOptimized).toBe(true)
      
      // Check metadata
      const clericMetadata = store.getSpellsMetadata('cleric')
      expect(clericMetadata.cached).toBe(true)
      expect(clericMetadata.spell_count).toBe(219)
      expect(clericMetadata._serverOptimized).toBe(true)
    })

    it('should handle server not ready during pre-hydration', async () => {
      // Mock server not ready
      const healthResponse = {
        ready_for_instant_responses: false,
        startup_complete: false
      }

      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse(healthResponse))
      mockAxios.default.post.mockResolvedValueOnce(mockAxiosResponse({ success: true }))

      const result = await store.preHydrateCache()

      expect(result).toBe(true)
      expect(mockAxios.default.post).toHaveBeenCalledWith(
        expect.stringContaining('/api/scrape-all'),
        {},
        expect.objectContaining({ timeout: 180000 })
      )
    })

    it('should handle pre-hydration errors gracefully', async () => {
      mockAxios.default.get.mockRejectedValueOnce(new Error('Network error'))

      const result = await store.preHydrateCache()

      expect(result).toBe(false)
      expect(store.isPreHydrating).toBe(false)
    })

    it('should track hydrated classes correctly', () => {
      // Add some data
      store.spellsData = {
        cleric: [{ name: 'Spell 1' }],
        wizard: [],
        druid: [{ name: 'Spell 2' }, { name: 'Spell 3' }]
      }

      const hydratedClasses = store.getHydratedClasses

      expect(hydratedClasses).toContain('cleric')
      expect(hydratedClasses).toContain('druid')
      expect(hydratedClasses).not.toContain('wizard') // Empty array
    })
  })

  describe('Enhanced Spell Fetching', () => {
    it('should detect placeholder data and fetch real data', async () => {
      // Set up placeholder data
      store.spellsData.cleric = [{
        _placeholder: true,
        _serverReady: true,
        _serverOptimized: true,
        name: 'Cleric spells ready on server',
        level: 0
      }]

      const realSpellData = mockSpellData
      const response = {
        spells: realSpellData,
        cached: true,
        last_updated: '2025-07-03T10:00:00Z',
        spell_count: 2
      }

      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse(response))

      const result = await store.fetchSpellsForClass('cleric')

      expect(mockAxios.default.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/spells/cleric'),
        expect.objectContaining({
          timeout: 10000, // Shorter timeout for server-optimized data
          headers: expect.objectContaining({
            'Accept': 'application/json'
          })
        })
      )

      expect(result).toEqual(realSpellData)
      expect(store.spellsData.cleric).toEqual(realSpellData)
    })

    it('should handle server optimization timeout differently', async () => {
      // Non-optimized data should use longer timeout
      const response = {
        spells: mockSpellData,
        cached: false,
        spell_count: 2
      }

      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse(response))

      await store.fetchSpellsForClass('cleric')

      expect(mockAxios.default.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/spells/cleric'),
        expect.objectContaining({
          timeout: 60000 // Longer timeout for fresh scraping
        })
      )
    })

    it('should prevent duplicate requests with active request tracking', async () => {
      const response = {
        spells: mockSpellData,
        spell_count: 2
      }

      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse(response))

      // Start multiple requests simultaneously
      const promise1 = store.fetchSpellsForClass('cleric')
      const promise2 = store.fetchSpellsForClass('cleric')
      const promise3 = store.fetchSpellsForClass('cleric')

      const results = await Promise.all([promise1, promise2, promise3])

      // Should only make one API call
      expect(mockAxios.default.get).toHaveBeenCalledTimes(1)
      
      // All promises should resolve to the same data
      expect(results[0]).toEqual(results[1])
      expect(results[1]).toEqual(results[2])
    })

    it('should store comprehensive metadata from API response', async () => {
      const response = {
        spells: mockSpellData,
        cached: true,
        last_updated: '2025-07-03T10:00:00Z',
        spell_count: 219,
        expired: false,
        stale: false
      }

      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse(response))

      await store.fetchSpellsForClass('cleric')

      const metadata = store.getSpellsMetadata('cleric')
      expect(metadata.cached).toBe(true)
      expect(metadata.last_updated).toBe('2025-07-03T10:00:00Z')
      expect(metadata.spell_count).toBe(219)
      expect(metadata.expired).toBe(false)
      expect(metadata.stale).toBe(false)
    })

    it('should handle stale cache warnings', async () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      
      const response = {
        spells: mockSpellData,
        stale: true,
        message: 'Cache is stale, consider refreshing'
      }

      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse(response))

      await store.fetchSpellsForClass('cleric')

      expect(consoleWarnSpy).toHaveBeenCalledWith('Stale data warning: Cache is stale, consider refreshing')
      
      consoleWarnSpy.mockRestore()
    })
  })

  describe('Force Refresh Functionality', () => {
    it('should clear memory and trigger server refresh', async () => {
      // Set up initial data
      store.spellsData = { cleric: [{ name: 'Old spell' }] }
      store.spellsMetadata = { cleric: { cached: true } }

      // Mock successful server refresh
      const healthResponse = {
        ready_for_instant_responses: true,
        startup_complete: true
      }
      
      const cacheStatusResponse = {
        cleric: { cached: true, spell_count: 219, last_updated: '2025-07-03T11:00:00Z' },
        _config: {}
      }

      mockAxios.default.post.mockResolvedValueOnce(mockAxiosResponse({ success: true }))
      mockAxios.default.get
        .mockResolvedValueOnce(mockAxiosResponse(healthResponse))
        .mockResolvedValueOnce(mockAxiosResponse(cacheStatusResponse))

      const result = await store.forceRefreshAllData()

      expect(result).toBe(true)
      expect(mockAxios.default.post).toHaveBeenCalledWith(
        expect.stringContaining('/api/scrape-all'),
        {},
        expect.objectContaining({ timeout: 300000 })
      )

      // Should have new placeholder data
      expect(store.isClassHydrated('cleric')).toBe(true)
      const clericData = store.getSpellsForClass('cleric')
      expect(clericData[0]._placeholder).toBe(true)
    })

    it('should handle force refresh errors', async () => {
      mockAxios.default.post.mockRejectedValueOnce(new Error('Server error'))

      await expect(store.forceRefreshAllData()).rejects.toThrow('Server error')
    })
  })
})