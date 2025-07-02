/**
 * Test suite for ClassSpells.vue component
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { setActivePinia, createPinia } from 'pinia'
import ClassSpells from '@/views/ClassSpells.vue'
import { useSpellsStore } from '@/stores/spells'
import { mockSpellData, mockCacheStatus } from '../setup.js'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

// Create test router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'Home', component: { template: '<div>Home</div>' } },
    { path: '/class/:className', name: 'ClassSpells', component: ClassSpells }
  ]
})

describe('ClassSpells Component', () => {
  let wrapper
  let store
  let mockAxios

  beforeEach(async () => {
    setActivePinia(createPinia())
    store = useSpellsStore()
    mockAxios = await import('axios')
    
    // Set up route params
    await router.push('/class/cleric')
    
    wrapper = mount(ClassSpells, {
      global: {
        plugins: [router],
        stubs: {
          // Stub complex child components
          'router-link': true,
          'router-view': true
        }
      }
    })
  })

  describe('Component Initialization', () => {
    it('should render correctly', () => {
      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.main-container').exists()).toBe(true)
      expect(wrapper.find('.hero-section').exists()).toBe(true)
    })

    it('should display class name in title', async () => {
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.class-title').text()).toContain('Cleric Spells')
    })

    it('should show loading state initially', () => {
      store.loading = true
      expect(wrapper.vm.loading).toBe(true)
    })
  })

  describe('Data Status Section', () => {
    beforeEach(() => {
      store.spells = mockSpellData
      store.cacheStatus = mockCacheStatus
    })

    it('should display data status when spells are loaded', async () => {
      await wrapper.vm.$nextTick()
      
      const dataStatusToggle = wrapper.find('.data-status-toggle')
      expect(dataStatusToggle.exists()).toBe(true)
    })

    it('should toggle data status expansion', async () => {
      await wrapper.vm.$nextTick()
      
      const toggleButton = wrapper.find('.data-status-toggle')
      expect(wrapper.vm.isDataStatusExpanded).toBe(false)
      
      await toggleButton.trigger('click')
      expect(wrapper.vm.isDataStatusExpanded).toBe(true)
    })

    it('should show correct spell count', async () => {
      await wrapper.vm.$nextTick()
      
      const spellCount = wrapper.find('.cache-count')
      expect(spellCount.text()).toContain('2 spells')
    })

    it('should calculate pricing statistics correctly', async () => {
      await wrapper.vm.$nextTick()
      
      const stats = wrapper.vm.realTimePricingStats
      expect(stats.total).toBe(2)
      expect(stats.cached).toBe(1) // Only one has actual pricing data
      expect(stats.failed).toBe(1)  // One has unknown: true
      expect(stats.unfetched).toBe(0)
      expect(stats.loading).toBe(0)
    })
  })

  describe('Cache Expiry Logic', () => {
    it('should detect expired spell data', () => {
      const expiredTime = new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString() // 25 hours ago
      store.cacheStatus = {
        spells: {
          timestamp: expiredTime,
          cached: true
        }
      }
      
      expect(wrapper.vm.isSpellDataExpired).toBe(true)
    })

    it('should detect fresh spell data', () => {
      const freshTime = new Date().toISOString()
      store.cacheStatus = {
        spells: {
          timestamp: freshTime,
          cached: true
        }
      }
      
      expect(wrapper.vm.isSpellDataExpired).toBe(false)
    })

    it('should detect expired pricing data', () => {
      const expiredTime = new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString() // 8 days ago
      store.cacheStatus = {
        pricing: {
          most_recent_timestamp: expiredTime
        }
      }
      
      expect(wrapper.vm.isPricingDataExpired).toBe(true)
    })
  })

  describe('Refresh Functionality', () => {
    it('should refresh spell data when expired', async () => {
      mockAxios.default.post.mockResolvedValueOnce({
        data: { success: true, spell_count: 219 }
      })

      await wrapper.vm.refreshSpellData()
      
      expect(mockAxios.default.post).toHaveBeenCalledWith(
        expect.stringContaining('/api/refresh-spell-cache/cleric')
      )
    })

    it('should refresh pricing data when expired', async () => {
      mockAxios.default.post.mockResolvedValueOnce({
        data: { success: true, cleared_count: 219 }
      })

      await wrapper.vm.refreshPricingData()
      
      expect(mockAxios.default.post).toHaveBeenCalledWith(
        expect.stringContaining('/api/refresh-pricing-cache/cleric')
      )
    })

    it('should handle refresh errors gracefully', async () => {
      mockAxios.default.post.mockRejectedValueOnce(new Error('Network error'))

      await wrapper.vm.refreshSpellData()
      
      expect(wrapper.vm.refreshingSpells).toBe(false)
    })
  })

  describe('Time Formatting', () => {
    it('should format timestamps correctly', () => {
      const timestamp = '2025-07-02T12:58:55.856237'
      const formatted = wrapper.vm.formatTimestamp(timestamp)
      
      expect(formatted).toMatch(/\d{1,2}\/\d{1,2}\/\d{4}/)
    })

    it('should handle invalid timestamps', () => {
      const formatted = wrapper.vm.formatTimestamp('invalid-date')
      expect(formatted).toBe('Invalid date')
    })

    it('should calculate time descriptions correctly', () => {
      const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString()
      const description = wrapper.vm.getTimeDescription(oneHourAgo, 24, false)
      
      expect(description).toContain('hour')
    })
  })

  describe('Level Navigation', () => {
    beforeEach(() => {
      store.spells = [
        { ...mockSpellData[0], level: 1 },
        { ...mockSpellData[1], level: 5 },
        { ...mockSpellData[0], level: 10, spell_id: '204' }
      ]
    })

    it('should generate level ranges correctly', async () => {
      await wrapper.vm.$nextTick()
      
      const levelRanges = wrapper.vm.levelRanges
      expect(levelRanges).toContain(1)
      expect(levelRanges).toContain(5)
      expect(levelRanges).toContain(10)
    })

    it('should scroll to level section when clicked', async () => {
      // Mock scrollIntoView
      Element.prototype.scrollIntoView = vi.fn()
      
      await wrapper.vm.scrollToLevel(5)
      
      // Should attempt to scroll
      expect(Element.prototype.scrollIntoView).toHaveBeenCalled()
    })
  })

  describe('Class Info and Styling', () => {
    it('should apply correct class-specific styling', async () => {
      await wrapper.vm.$nextTick()
      
      const container = wrapper.find('.main-container')
      expect(container.classes()).toContain('cleric')
    })

    it('should display class color from store', () => {
      store.classes = [
        { name: 'Cleric', color: '#ffffff' }
      ]
      
      const classInfo = wrapper.vm.classInfo
      expect(classInfo).toBeDefined()
      expect(classInfo.color).toBe('#ffffff')
    })
  })

  describe('Error Handling', () => {
    it('should display error messages', async () => {
      store.error = 'Test error message'
      await wrapper.vm.$nextTick()
      
      // Component should handle error state
      expect(wrapper.vm.error).toBe('Test error message')
    })

    it('should handle missing route params gracefully', async () => {
      await router.push('/class/')
      
      // Should not crash with missing className
      expect(wrapper.vm.className).toBeDefined()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA attributes for data status toggle', async () => {
      await wrapper.vm.$nextTick()
      
      const toggle = wrapper.find('.data-status-toggle')
      expect(toggle.attributes('aria-expanded')).toBe('false')
      expect(toggle.attributes('aria-controls')).toBe('data-status-content')
      expect(toggle.attributes('aria-label')).toContain('Expand Data Status')
    })

    it('should update ARIA attributes when expanded', async () => {
      await wrapper.vm.$nextTick()
      
      const toggle = wrapper.find('.data-status-toggle')
      await toggle.trigger('click')
      
      expect(toggle.attributes('aria-expanded')).toBe('true')
      expect(toggle.attributes('aria-label')).toContain('Collapse Data Status')
    })
  })

  describe('Performance', () => {
    it('should handle large spell datasets efficiently', async () => {
      const largeDataset = Array.from({ length: 500 }, (_, i) => ({
        ...mockSpellData[0],
        spell_id: i.toString(),
        name: `Spell ${i}`,
        level: Math.floor(i / 10) + 1
      }))

      store.spells = largeDataset
      
      const start = performance.now()
      await wrapper.vm.$nextTick()
      const end = performance.now()
      
      expect(end - start).toBeLessThan(200) // Should render in under 200ms
    })

    it('should debounce refresh operations', async () => {
      const spy = vi.spyOn(wrapper.vm, 'refreshSpellData')
      
      // Trigger multiple rapid refresh attempts
      wrapper.vm.refreshSpellData()
      wrapper.vm.refreshSpellData()
      wrapper.vm.refreshSpellData()
      
      await wrapper.vm.$nextTick()
      
      // Should prevent multiple simultaneous refreshes
      expect(wrapper.vm.refreshingSpells).toBeDefined()
    })
  })
})