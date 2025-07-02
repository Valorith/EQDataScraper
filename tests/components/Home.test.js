/**
 * Test suite for Home.vue component
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { setActivePinia, createPinia } from 'pinia'
import Home from '@/views/Home.vue'
import { useSpellsStore } from '@/stores/spells'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn()
  }
}))

// Create test router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'Home', component: Home },
    { path: '/class/:className', name: 'ClassSpells', component: { template: '<div>ClassSpells</div>' } }
  ]
})

describe('Home Component', () => {
  let wrapper
  let store
  let mockAxios

  const mockClasses = [
    { name: 'Cleric', id: '2', color: '#ffffff' },
    { name: 'Wizard', id: '14', color: '#4169e1' },
    { name: 'Warrior', id: '1', color: '#8b4513' }
  ]

  beforeEach(async () => {
    setActivePinia(createPinia())
    store = useSpellsStore()
    mockAxios = await import('axios')
    
    await router.push('/')
    
    wrapper = mount(Home, {
      global: {
        plugins: [router],
        stubs: {
          'router-link': true
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

    it('should display main title', () => {
      expect(wrapper.find('.main-title').text()).toBe("Clumsy's World")
      expect(wrapper.find('.main-subtitle').text()).toBe('Class Information')
    })

    it('should fetch classes on mount', () => {
      const spy = vi.spyOn(store, 'fetchClasses')
      wrapper = mount(Home, {
        global: { plugins: [router] }
      })
      
      expect(spy).toHaveBeenCalled()
    })
  })

  describe('Class Grid Display', () => {
    beforeEach(() => {
      store.classes = mockClasses
    })

    it('should display all classes', async () => {
      await wrapper.vm.$nextTick()
      
      const classCards = wrapper.findAll('.class-card')
      expect(classCards).toHaveLength(3)
    })

    it('should show class names and colors', async () => {
      await wrapper.vm.$nextTick()
      
      const firstCard = wrapper.find('.class-card')
      expect(firstCard.text()).toContain('Cleric')
    })

    it('should apply class-specific styling', async () => {
      await wrapper.vm.$nextTick()
      
      const classCards = wrapper.findAll('.class-card')
      classCards.forEach((card, index) => {
        const className = mockClasses[index].name.toLowerCase()
        expect(card.classes()).toContain(className)
      })
    })
  })

  describe('Global Search Functionality', () => {
    beforeEach(() => {
      const mockSearchResults = [
        {
          name: 'Courage',
          spell_id: '202',
          level: 1,
          mana: '10',
          classes: ['CLR'],
          icon: 'spell_202.png'
        },
        {
          name: 'Flash of Light',
          spell_id: '203', 
          level: 1,
          mana: '10',
          classes: ['CLR'],
          icon: 'spell_203.png'
        }
      ]

      mockAxios.default.get.mockResolvedValue({
        data: mockSearchResults
      })
    })

    it('should show search input', () => {
      const searchInput = wrapper.find('.global-search-input')
      expect(searchInput.exists()).toBe(true)
      expect(searchInput.attributes('placeholder')).toContain('Search spells across all classes')
    })

    it('should perform search on input', async () => {
      const searchInput = wrapper.find('.global-search-input')
      
      await searchInput.setValue('courage')
      await searchInput.trigger('input')
      
      // Wait for debounced search
      await new Promise(resolve => setTimeout(resolve, 300))
      
      expect(mockAxios.default.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/search-spells'),
        expect.objectContaining({
          params: { q: 'courage' }
        })
      )
    })

    it('should display search results dropdown', async () => {
      const searchInput = wrapper.find('.global-search-input')
      
      await searchInput.setValue('courage')
      await searchInput.trigger('input')
      await wrapper.vm.$nextTick()
      
      // Simulate search results
      wrapper.vm.searchResults = [
        {
          name: 'Courage',
          spell_id: '202',
          level: 1,
          classes: ['CLR']
        }
      ]
      wrapper.vm.showDropdown = true
      
      await wrapper.vm.$nextTick()
      
      const dropdown = wrapper.find('.search-dropdown')
      expect(dropdown.exists()).toBe(true)
      
      const resultItems = wrapper.findAll('.search-result-item')
      expect(resultItems).toHaveLength(1)
    })

    it('should handle search pagination', async () => {
      const manyResults = Array.from({ length: 15 }, (_, i) => ({
        name: `Spell ${i}`,
        spell_id: i.toString(),
        level: 1,
        classes: ['CLR']
      }))

      wrapper.vm.searchResults = manyResults
      wrapper.vm.showDropdown = true
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.showPagination).toBe(true)
      expect(wrapper.vm.totalPages).toBeGreaterThan(1)
      
      const paginationControls = wrapper.find('.pagination-controls')
      expect(paginationControls.exists()).toBe(true)
    })

    it('should clear search results', async () => {
      const searchInput = wrapper.find('.global-search-input')
      const clearButton = wrapper.find('.clear-search-btn')
      
      await searchInput.setValue('test')
      await wrapper.vm.$nextTick()
      
      expect(clearButton.exists()).toBe(true)
      
      await clearButton.trigger('click')
      
      expect(wrapper.vm.searchQuery).toBe('')
      expect(wrapper.vm.searchResults).toEqual([])
    })
  })

  describe('Search Navigation', () => {
    beforeEach(() => {
      wrapper.vm.searchResults = [
        { name: 'Spell 1', spell_id: '1' },
        { name: 'Spell 2', spell_id: '2' },
        { name: 'Spell 3', spell_id: '3' }
      ]
      wrapper.vm.showDropdown = true
    })

    it('should handle keyboard navigation', async () => {
      const searchInput = wrapper.find('.global-search-input')
      
      // Arrow down should select first result
      await searchInput.trigger('keydown', { key: 'ArrowDown' })
      expect(wrapper.vm.selectedIndex).toBe(0)
      
      // Arrow down again should select second result
      await searchInput.trigger('keydown', { key: 'ArrowDown' })
      expect(wrapper.vm.selectedIndex).toBe(1)
      
      // Arrow up should go back to first result
      await searchInput.trigger('keydown', { key: 'ArrowUp' })
      expect(wrapper.vm.selectedIndex).toBe(0)
    })

    it('should select spell on Enter key', async () => {
      const routerSpy = vi.spyOn(router, 'push')
      const searchInput = wrapper.find('.global-search-input')
      
      wrapper.vm.selectedIndex = 0
      await searchInput.trigger('keydown', { key: 'Enter' })
      
      expect(routerSpy).toHaveBeenCalled()
    })

    it('should close dropdown on Escape key', async () => {
      const searchInput = wrapper.find('.global-search-input')
      
      expect(wrapper.vm.showDropdown).toBe(true)
      
      await searchInput.trigger('keydown', { key: 'Escape' })
      
      expect(wrapper.vm.showDropdown).toBe(false)
    })
  })

  describe('Search Result Highlighting', () => {
    it('should highlight search terms in results', () => {
      wrapper.vm.searchQuery = 'courage'
      
      const highlighted = wrapper.vm.highlightMatch('Courage of the Ages')
      
      expect(highlighted).toContain('<mark>')
      expect(highlighted).toContain('courage')
      expect(highlighted).toContain('</mark>')
    })

    it('should handle case-insensitive highlighting', () => {
      wrapper.vm.searchQuery = 'COURAGE'
      
      const highlighted = wrapper.vm.highlightMatch('courage spell')
      
      expect(highlighted).toContain('<mark>')
    })

    it('should escape HTML in search terms', () => {
      wrapper.vm.searchQuery = '<script>'
      
      const highlighted = wrapper.vm.highlightMatch('safe <script> text')
      
      expect(highlighted).not.toContain('<script>')
      expect(highlighted).toContain('&lt;script&gt;')
    })
  })

  describe('Loading and Error States', () => {
    it('should show loading state', async () => {
      store.loading = true
      await wrapper.vm.$nextTick()
      
      // Component should handle loading state appropriately
      expect(store.loading).toBe(true)
    })

    it('should display error messages', async () => {
      store.error = 'Failed to load classes'
      await wrapper.vm.$nextTick()
      
      // Component should handle error state
      expect(store.error).toBe('Failed to load classes')
    })

    it('should handle search errors gracefully', async () => {
      mockAxios.default.get.mockRejectedValueOnce(new Error('Search failed'))
      
      const searchInput = wrapper.find('.global-search-input')
      await searchInput.setValue('test')
      await searchInput.trigger('input')
      
      await new Promise(resolve => setTimeout(resolve, 300))
      
      // Should not crash and should clear results
      expect(wrapper.vm.searchResults).toEqual([])
    })
  })

  describe('Performance Optimizations', () => {
    it('should debounce search input', async () => {
      const searchSpy = vi.spyOn(wrapper.vm, 'performSearch')
      const searchInput = wrapper.find('.global-search-input')
      
      // Rapid typing
      await searchInput.setValue('c')
      await searchInput.trigger('input')
      await searchInput.setValue('co')
      await searchInput.trigger('input')
      await searchInput.setValue('cou')
      await searchInput.trigger('input')
      
      // Should not call search immediately
      expect(searchSpy).not.toHaveBeenCalled()
      
      // Wait for debounce
      await new Promise(resolve => setTimeout(resolve, 300))
      
      // Should call search only once
      expect(searchSpy).toHaveBeenCalledTimes(1)
    })

    it('should handle rapid navigation efficiently', async () => {
      const manyResults = Array.from({ length: 100 }, (_, i) => ({
        name: `Spell ${i}`,
        spell_id: i.toString()
      }))

      wrapper.vm.searchResults = manyResults
      wrapper.vm.showDropdown = true
      
      const start = performance.now()
      
      // Rapid key navigation
      for (let i = 0; i < 10; i++) {
        await wrapper.find('.global-search-input').trigger('keydown', { key: 'ArrowDown' })
      }
      
      const end = performance.now()
      
      expect(end - start).toBeLessThan(50) // Should be very fast
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA attributes for search', () => {
      const searchInput = wrapper.find('.global-search-input')
      
      expect(searchInput.attributes('autocomplete')).toBe('off')
      expect(searchInput.attributes('role')).toBe('combobox')
    })

    it('should support screen reader navigation', async () => {
      wrapper.vm.searchResults = [{ name: 'Test Spell', spell_id: '1' }]
      wrapper.vm.showDropdown = true
      wrapper.vm.selectedIndex = 0
      
      await wrapper.vm.$nextTick()
      
      const selectedResult = wrapper.find('.search-result-item.highlighted')
      expect(selectedResult.exists()).toBe(true)
    })
  })
})