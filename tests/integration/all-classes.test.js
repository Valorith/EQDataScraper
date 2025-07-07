/**
 * Integration tests for all EverQuest classes
 * These tests ensure every class works properly and catches issues like the shadowknight HTML bug
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

import axios from 'axios'

describe('All EverQuest Classes Integration Tests', () => {
  let store

  // All EQ classes as defined in the application
  const ALL_EQ_CLASSES = [
    'Warrior', 'Cleric', 'Paladin', 'Ranger', 'ShadowKnight', 'Druid',
    'Monk', 'Bard', 'Rogue', 'Shaman', 'Necromancer', 'Wizard',
    'Magician', 'Enchanter', 'Beastlord', 'Berserker'
  ]

  beforeEach(async () => {
    setActivePinia(createPinia())
    store = useSpellsStore()
    vi.clearAllMocks()
  })

  describe('Class Name Normalization for All Classes', () => {
    it('should handle all EQ class names with various case formats', async () => {
      // Test each class with multiple case variations
      for (const className of ALL_EQ_CLASSES) {
        const testCases = [
          className.toLowerCase(),
          className.toUpperCase(),
          className, // Original case
          className.charAt(0).toLowerCase() + className.slice(1) // camelCase
        ]

        for (const testCase of testCases) {
          const response = {
            spells: mockSpellData,
            cached: true,
            last_updated: '2025-07-03T10:00:00Z',
            spell_count: 2
          }

          axios.get.mockResolvedValueOnce(mockAxiosResponse(response))

          const result = await store.fetchSpellsForClass(testCase)

          // Verify API call was made with lowercase class name
          expect(axios.get).toHaveBeenCalledWith(
            expect.stringContaining(`/api/spells/${className.toLowerCase()}`),
            expect.any(Object)
          )

          // Verify data was stored correctly
          expect(result).toEqual(mockSpellData)
          expect(store.spellsData[className.toLowerCase()]).toEqual(mockSpellData)

          vi.clearAllMocks()
        }
      }
    })

    it('should specifically test ShadowKnight variations that caused the bug', async () => {
      const shadowknightVariations = [
        'shadowknight',
        'ShadowKnight', 
        'SHADOWKNIGHT',
        'Shadowknight',
        'shadowKnight',
        'sHaDoWkNiGhT'
      ]

      for (const variation of shadowknightVariations) {
        const response = {
          spells: mockSpellData,
          cached: true,
          last_updated: '2025-07-03T10:00:00Z',
          spell_count: 2
        }

        axios.get.mockResolvedValueOnce(mockAxiosResponse(response))

        const result = await store.fetchSpellsForClass(variation)

        // Should always call API with 'shadowknight' (lowercase)
        expect(axios.get).toHaveBeenCalledWith(
          expect.stringContaining('/api/spells/shadowknight'),
          expect.any(Object)
        )

        expect(result).toEqual(mockSpellData)
        vi.clearAllMocks()
      }
    })
  })

  describe('HTML Response Detection for All Classes', () => {
    it('should detect HTML responses for any class and throw appropriate errors', async () => {
      const htmlErrorResponse = '<!DOCTYPE html><html><head><title>Error</title></head><body>Not Found</body></html>'
      
      // Test a few representative classes including shadowknight
      const testClasses = ['shadowknight', 'cleric', 'wizard', 'beastlord']

      for (const className of testClasses) {
        axios.get.mockResolvedValueOnce({
          data: htmlErrorResponse,
          status: 200,
          headers: { 'content-type': 'text/html' }
        })

        await expect(store.fetchSpellsForClass(className)).rejects.toThrow('Invalid response format from server')
        expect(store.error).toContain('Invalid response format from server')

        // Reset error state
        store.error = null
        vi.clearAllMocks()
      }
    })

    it('should handle mixed HTML/JSON responses that might occur with routing issues', async () => {
      // Simulate the exact scenario from the bug report
      const htmlPage = `<!DOCTYPE html>
<html>
<head>
  <title>EQ Data Scraper</title>
</head>
<body>
  <div id="app"></div>
</body>
</html>`

      axios.get.mockResolvedValueOnce({
        status: 200,
        data: htmlPage,
        headers: { 'content-type': 'text/html' }
      })

      await expect(store.fetchSpellsForClass('shadowknight')).rejects.toThrow()
      expect(store.error).toBeTruthy()
    })
  })

  describe('API Response Format Validation for All Classes', () => {
    it('should validate that all classes return proper JSON structure', async () => {
      for (const className of ALL_EQ_CLASSES) {
        const validResponse = {
          spells: [
            { name: 'Test Spell', level: 1, spell_id: '12345', mana: 50 },
            { name: 'Another Spell', level: 5, spell_id: '12346', mana: 100 }
          ],
          cached: true,
          last_updated: '2025-07-03T10:00:00Z',
          spell_count: 2,
          expired: false
        }

        axios.get.mockResolvedValueOnce(mockAxiosResponse(validResponse))

        const result = await store.fetchSpellsForClass(className)

        // Verify response structure
        expect(Array.isArray(result)).toBe(true)
        expect(result).toEqual(validResponse.spells)

        // Verify metadata was stored
        const metadata = store.getSpellsMetadata(className)
        expect(metadata.cached).toBe(true)
        expect(metadata.spell_count).toBe(2)
        expect(metadata.last_updated).toBe('2025-07-03T10:00:00Z')

        vi.clearAllMocks()
      }
    })

    it('should handle malformed API responses gracefully for all classes', async () => {
      const malformedResponses = [
        null,
        undefined,
        '',
        'not json',
        { wrong: 'structure' },
        { spells: 'not an array' },
        { spells: null }
      ]

      for (const malformedResponse of malformedResponses) {
        axios.get.mockResolvedValueOnce(mockAxiosResponse(malformedResponse))

        await expect(store.fetchSpellsForClass('shadowknight')).rejects.toThrow()
        
        vi.clearAllMocks()
      }
    })
  })

  describe('Class Lookup and Validation', () => {
    it('should find all classes in the store class list', () => {
      // Verify all classes are properly defined in the store
      for (const className of ALL_EQ_CLASSES) {
        const classInfo = store.getClassByName(className)
        expect(classInfo).toBeTruthy()
        expect(classInfo.name).toBe(className)
        expect(classInfo.id).toBeGreaterThan(0)
        expect(classInfo.color).toBeTruthy()
      }
    })

    it('should handle case-insensitive class lookups', () => {
      for (const className of ALL_EQ_CLASSES) {
        const variations = [
          className.toLowerCase(),
          className.toUpperCase(),
          className
        ]

        for (const variation of variations) {
          const classInfo = store.getClassByName(variation)
          expect(classInfo).toBeTruthy()
          expect(classInfo.name).toBe(className)
        }
      }
    })
  })

  describe('Error Recovery and Resilience', () => {
    it('should recover from network errors for any class', async () => {
      const networkError = new Error('Network Error')
      networkError.request = {} // This indicates a network error
      networkError.code = 'NETWORK_ERROR'

      for (const className of ['shadowknight', 'cleric', 'wizard']) {
        axios.get.mockRejectedValueOnce(networkError)

        await expect(store.fetchSpellsForClass(className)).rejects.toThrow('Unable to connect to server')

        // Reset for next test
        store.error = null
        vi.clearAllMocks()
      }
    })

    it('should handle timeout errors appropriately', async () => {
      const timeoutError = new Error('timeout of 60000ms exceeded')
      timeoutError.code = 'ECONNABORTED'

      axios.get.mockRejectedValueOnce(timeoutError)

      await expect(store.fetchSpellsForClass('shadowknight')).rejects.toThrow('Request timed out')
    })
  })

  describe('Performance with All Classes', () => {
    it('should handle concurrent requests for multiple classes', async () => {
      const testClasses = ['shadowknight', 'cleric', 'wizard', 'paladin']
      const responses = testClasses.map(() => ({
        spells: mockSpellData,
        cached: true,
        spell_count: 2
      }))

      // Mock responses for all classes
      responses.forEach(response => {
        axios.get.mockResolvedValueOnce(mockAxiosResponse(response))
      })

      // Start all requests concurrently
      const promises = testClasses.map(className => store.fetchSpellsForClass(className))
      const results = await Promise.all(promises)

      // Verify all succeeded
      results.forEach((result, index) => {
        expect(result).toEqual(mockSpellData)
        expect(store.spellsData[testClasses[index]]).toEqual(mockSpellData)
      })

      // Should have made one call per class
      expect(axios.get).toHaveBeenCalledTimes(testClasses.length)
    })
  })
})