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
})