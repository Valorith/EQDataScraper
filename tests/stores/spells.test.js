/**
 * Test suite for Pinia spells store
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSpellsStore } from '@/stores/spells'
import { mockAxiosResponse, mockSpellData } from '../setup.js'

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
    vi.clearAllMocks()
  })

  describe('State Management', () => {
    it('should initialize with correct default state', () => {
      expect(store.classes).toHaveLength(16) // 16 EQ classes
      expect(store.spellsData).toEqual({})
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.spellsMetadata).toEqual({})
    })

    it('should handle loading state correctly', () => {
      store.loading = true
      expect(store.loading).toBe(true)
      
      store.loading = false
      expect(store.loading).toBe(false)
    })

    it('should handle error state correctly', () => {
      const errorMessage = 'Test error'
      store.error = errorMessage
      expect(store.error).toBe(errorMessage)
      
      store.error = null
      expect(store.error).toBeNull()
    })
  })

  describe('Class Management', () => {
    it('should have all EQ classes predefined', () => {
      expect(store.classes).toHaveLength(16)
      const classNames = store.classes.map(c => c.name)
      expect(classNames).toContain('Warrior')
      expect(classNames).toContain('Cleric')
      expect(classNames).toContain('ShadowKnight')
      expect(classNames).toContain('Wizard')
    })

    it('should find class by name case-insensitively', () => {
      const cleric1 = store.getClassByName('Cleric')
      const cleric2 = store.getClassByName('cleric')
      const cleric3 = store.getClassByName('CLERIC')

      expect(cleric1).toBeTruthy()
      expect(cleric2).toBeTruthy()
      expect(cleric3).toBeTruthy()
      expect(cleric1.name).toBe('Cleric')
      expect(cleric2.name).toBe('Cleric')
      expect(cleric3.name).toBe('Cleric')
    })

    it('should find ShadowKnight by various case formats - critical test', () => {
      const variations = ['shadowknight', 'ShadowKnight', 'SHADOWKNIGHT', 'Shadowknight']
      
      for (const variation of variations) {
        const shadowknight = store.getClassByName(variation)
        expect(shadowknight).toBeTruthy()
        expect(shadowknight.name).toBe('ShadowKnight')
        expect(shadowknight.id).toBe(5)
      }
    })
  })

  describe('Spell Fetching - Critical HTML Bug Tests', () => {
    it('should fetch and store spells for a class', async () => {
      const mockResponse = {
        spells: mockSpellData,
        cached: true,
        last_updated: '2025-07-02T12:58:55.856237',
        spell_count: 2
      }

      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse(mockResponse))

      const result = await store.fetchSpellsForClass('cleric')

      expect(result).toEqual(mockSpellData)
      expect(store.getSpellsForClass('cleric')).toEqual(mockSpellData)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('should handle ShadowKnight class name normalization - critical', async () => {
      const shadowknightSpells = [
        { name: 'Harm Touch', level: 1, spell_id: '90001' },
        { name: 'Death Pact', level: 20, spell_id: '90002' }
      ]
      const response = {
        spells: shadowknightSpells,
        cached: true,
        last_updated: '2025-07-03T10:00:00Z',
        spell_count: 2
      }

      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse(response))

      // Test that ShadowKnight gets normalized to lowercase for API call
      const result = await store.fetchSpellsForClass('ShadowKnight')

      expect(mockAxios.default.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/spells/shadowknight'), // Should be lowercase
        expect.any(Object)
      )

      expect(result).toEqual(shadowknightSpells)
      expect(store.getSpellsForClass('shadowknight')).toEqual(shadowknightSpells) // Stored with lowercase key
    })

    it('should detect and handle HTML responses gracefully - prevents original bug', async () => {
      const htmlResponse = '<!DOCTYPE html><html><head><title>Error 404</title></head><body>Not Found</body></html>'
      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse(htmlResponse))

      await expect(store.fetchSpellsForClass('shadowknight')).rejects.toThrow('Invalid response format from server')
    })

    it('should handle axios returning HTML content with proper error detection', async () => {
      // Mock axios returning HTML when it should return JSON (common routing issue)
      const htmlErrorPage = `<!DOCTYPE html>
        <html>
          <head><title>404 Not Found</title></head>
          <body><h1>Page Not Found</h1></body>
        </html>`
      
      mockAxios.default.get.mockResolvedValueOnce({
        status: 200,
        data: htmlErrorPage,
        headers: { 'content-type': 'text/html' }
      })

      await expect(store.fetchSpellsForClass('shadowknight')).rejects.toThrow()
    })

    it('should handle fetch spells error', async () => {
      mockAxios.default.get.mockRejectedValueOnce(new Error('Server error'))

      await expect(store.fetchSpellsForClass('cleric')).rejects.toThrow()
      expect(store.loading).toBe(false)
    })
  })

  describe('Getters and Computed Properties', () => {
    beforeEach(() => {
      // Set up test data
      store.spellsData = {
        cleric: mockSpellData,
        shadowknight: [
          { name: 'Harm Touch', level: 1, spell_id: '90001' },
          { name: 'Death Pact', level: 20, spell_id: '90002' }
        ]
      }
      store.spellsMetadata = {
        cleric: {
          cached: true,
          spell_count: 2,
          last_updated: '2025-07-03T10:00:00Z'
        }
      }
    })

    it('should get spells for class correctly', () => {
      const clericSpells = store.getSpellsForClass('cleric')
      expect(clericSpells).toEqual(mockSpellData)
      
      const shadowknightSpells = store.getSpellsForClass('shadowknight')
      expect(shadowknightSpells).toHaveLength(2)
      
      // Test case insensitivity
      const clericSpells2 = store.getSpellsForClass('CLERIC')
      expect(clericSpells2).toEqual(mockSpellData)
    })

    it('should get metadata for class correctly', () => {
      const metadata = store.getSpellsMetadata('cleric')
      expect(metadata.cached).toBe(true)
      expect(metadata.spell_count).toBe(2)
    })

    it('should check if class is hydrated', () => {
      expect(store.isClassHydrated('cleric')).toBe(true)
      expect(store.isClassHydrated('shadowknight')).toBe(true)
      expect(store.isClassHydrated('wizard')).toBeFalsy() // Could be false or undefined
    })

    it('should get list of hydrated classes', () => {
      const hydrated = store.getHydratedClasses
      expect(hydrated).toContain('cleric')
      expect(hydrated).toContain('shadowknight')
      expect(hydrated).not.toContain('wizard')
    })
  })

  describe('Server Optimization and Pre-hydration', () => {
    it('should handle server warmup with retry logic', async () => {
      // First attempt fails, second succeeds
      mockAxios.default.get.mockRejectedValueOnce(new Error('Connection failed'))
      mockAxios.default.get.mockResolvedValueOnce(mockAxiosResponse({ status: 'healthy' }))

      const result = await store.warmupBackend()

      expect(result).toBe(true)
      expect(mockAxios.default.get).toHaveBeenCalledTimes(2)
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
        shadowknight: { cached: true, spell_count: 117, last_updated: '2025-07-03T10:00:00Z' },
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
      expect(store.isClassHydrated('shadowknight')).toBe(true)
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
    })

    it('should handle force refresh errors', async () => {
      mockAxios.default.post.mockRejectedValueOnce(new Error('Server error'))

      await expect(store.forceRefreshAllData()).rejects.toThrow('Server error')
    })
  })

  describe('Request Deduplication and Performance', () => {
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
  })
})