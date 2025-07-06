/**
 * Tests for Recent Activity component in Admin Dashboard
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import AdminDashboard from '../../src/views/AdminDashboard.vue'

// Mock API calls
const mockApiGet = vi.fn()
vi.mock('axios', () => ({
  default: {
    get: mockApiGet
  }
}))

// Mock router
const mockRouter = {
  push: vi.fn()
}

vi.mock('vue-router', () => ({
  useRouter: () => mockRouter
}))

// Mock user store
const mockUserStore = {
  accessToken: 'test-admin-token',
  user: { 
    id: 1, 
    email: 'admin@test.com', 
    role: 'admin',
    is_admin: true 
  },
  isAuthenticated: true,
  isAdmin: true
}

vi.mock('../stores/userStore', () => ({
  useUserStore: () => mockUserStore
}))

describe('Recent Activity Component', () => {
  let wrapper
  let pinia

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    vi.clearAllMocks()
    
    // Default API responses
    mockApiGet.mockImplementation((url) => {
      if (url.includes('/api/admin/stats')) {
        return Promise.resolve({
          data: { totalUsers: 5, activeToday: 3, adminUsers: 2 }
        })
      }
      if (url.includes('/api/admin/activities')) {
        return Promise.resolve({
          data: {
            success: true,
            data: {
              activities: [],
              total_count: 0
            }
          }
        })
      }
      if (url.includes('/api/cache-status')) {
        return Promise.resolve({
          data: { healthy: true, cachedClasses: 16 }
        })
      }
      if (url.includes('/api/health')) {
        return Promise.resolve({
          data: { status: 'healthy' }
        })
      }
      return Promise.resolve({ data: {} })
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Recent Activity Display', () => {
    it('should render Recent Activity section', async () => {
      wrapper = mount(AdminDashboard, {
        global: {
          plugins: [pinia]
        }
      })

      await nextTick()
      await wrapper.vm.$nextTick()

      const recentActivitySection = wrapper.find('.recent-activity')
      expect(recentActivitySection.exists()).toBe(true)
      
      const title = recentActivitySection.find('h2')
      expect(title.text()).toBe('Recent Activity')
    })

    it('should show empty state message when no activities', async () => {
      wrapper = mount(AdminDashboard, {
        global: {
          plugins: [pinia]
        }
      })

      await nextTick()
      await wrapper.vm.$nextTick()

      const noActivity = wrapper.find('.no-activity')
      expect(noActivity.exists()).toBe(true)
      expect(noActivity.text()).toContain('No activity logged yet')
      expect(noActivity.text()).toContain('Activity will appear here when users log in')
    })

    it('should display activities when data is available', async () => {
      const mockActivities = [
        {
          id: 1,
          action: 'login',
          user_id: 1,
          user_display: 'Test User',
          userAvatar: 'https://example.com/avatar.jpg',
          description: 'Test User logged in',
          timestamp: new Date().toISOString(),
          type: 'login'
        },
        {
          id: 2,
          action: 'spell_search',
          user_id: 1,
          user_display: 'Test User',
          userAvatar: 'https://example.com/avatar.jpg',
          description: 'Test User searched for spells: "heal"',
          timestamp: new Date().toISOString(),
          type: 'spell_search'
        }
      ]

      mockApiGet.mockImplementation((url) => {
        if (url.includes('/api/admin/activities')) {
          return Promise.resolve({
            data: {
              success: true,
              data: {
                activities: mockActivities,
                total_count: 2
              }
            }
          })
        }
        return Promise.resolve({ data: {} })
      })

      wrapper = mount(AdminDashboard, {
        global: {
          plugins: [pinia]
        }
      })

      await nextTick()
      await wrapper.vm.$nextTick()
      // Wait for API calls to complete
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      const activityItems = wrapper.findAll('.activity-item')
      expect(activityItems.length).toBe(2)
      
      // Check first activity
      const firstActivity = activityItems[0]
      expect(firstActivity.text()).toContain('Test User logged in')
      
      // Check activity has avatar
      const avatar = firstActivity.find('.activity-avatar img')
      expect(avatar.exists()).toBe(true)
    })

    it('should display system activities with icons instead of avatars', async () => {
      const systemActivity = {
        id: 1,
        action: 'cache_refresh',
        user_id: null,
        user_display: 'System',
        userAvatar: null,
        description: 'System refreshed cache',
        timestamp: new Date().toISOString(),
        type: 'cache_refresh'
      }

      mockApiGet.mockImplementation((url) => {
        if (url.includes('/api/admin/activities')) {
          return Promise.resolve({
            data: {
              success: true,
              data: {
                activities: [systemActivity],
                total_count: 1
              }
            }
          })
        }
        return Promise.resolve({ data: {} })
      })

      wrapper = mount(AdminDashboard, {
        global: {
          plugins: [pinia]
        }
      })

      await nextTick()
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      const activityItem = wrapper.find('.activity-item')
      expect(activityItem.exists()).toBe(true)
      
      // Should have icon instead of avatar for system activities
      const icon = activityItem.find('.activity-icon')
      expect(icon.exists()).toBe(true)
      
      const avatar = activityItem.find('.activity-avatar')
      expect(avatar.exists()).toBe(false)
    })
  })

  describe('Activity API Integration', () => {
    it('should call activities API with correct parameters', async () => {
      wrapper = mount(AdminDashboard, {
        global: {
          plugins: [pinia]
        }
      })

      await nextTick()
      await wrapper.vm.$nextTick()

      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining('/api/admin/activities'),
        expect.objectContaining({
          headers: { Authorization: 'Bearer test-admin-token' },
          params: { limit: 10 }
        })
      )
    })

    it('should handle API errors gracefully', async () => {
      mockApiGet.mockImplementation((url) => {
        if (url.includes('/api/admin/activities')) {
          return Promise.reject(new Error('API Error'))
        }
        return Promise.resolve({ data: {} })
      })

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      wrapper = mount(AdminDashboard, {
        global: {
          plugins: [pinia]
        }
      })

      await nextTick()
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      // Should still show empty state on API error
      const noActivity = wrapper.find('.no-activity')
      expect(noActivity.exists()).toBe(true)

      consoleSpy.mockRestore()
    })

    it('should refresh activities periodically', async () => {
      vi.useFakeTimers()

      wrapper = mount(AdminDashboard, {
        global: {
          plugins: [pinia]
        }
      })

      await nextTick()
      await wrapper.vm.$nextTick()

      const initialCallCount = mockApiGet.mock.calls.filter(call => 
        call[0].includes('/api/admin/activities')
      ).length

      // Fast forward 60 seconds (activity refresh interval)
      vi.advanceTimersByTime(60000)
      await wrapper.vm.$nextTick()

      const afterCallCount = mockApiGet.mock.calls.filter(call => 
        call[0].includes('/api/admin/activities')
      ).length

      expect(afterCallCount).toBeGreaterThan(initialCallCount)

      vi.useRealTimers()
    })
  })

  describe('Activity Formatting', () => {
    it('should format activity timestamps correctly', async () => {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString()
      const activity = {
        id: 1,
        description: 'Test activity',
        timestamp: fiveMinutesAgo,
        type: 'test'
      }

      mockApiGet.mockImplementation((url) => {
        if (url.includes('/api/admin/activities')) {
          return Promise.resolve({
            data: {
              success: true,
              data: {
                activities: [activity],
                total_count: 1
              }
            }
          })
        }
        return Promise.resolve({ data: {} })
      })

      wrapper = mount(AdminDashboard, {
        global: {
          plugins: [pinia]
        }
      })

      await nextTick()
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      const timeElement = wrapper.find('.activity-time')
      expect(timeElement.exists()).toBe(true)
      expect(timeElement.text()).toMatch(/\d+m ago/)
    })

    it('should handle different activity types with correct icons', async () => {
      const activities = [
        { id: 1, type: 'login', description: 'Login activity' },
        { id: 2, type: 'cache_refresh', description: 'Cache activity' },
        { id: 3, type: 'spell_search', description: 'Search activity' }
      ]

      mockApiGet.mockImplementation((url) => {
        if (url.includes('/api/admin/activities')) {
          return Promise.resolve({
            data: {
              success: true,
              data: {
                activities: activities,
                total_count: 3
              }
            }
          })
        }
        return Promise.resolve({ data: {} })
      })

      wrapper = mount(AdminDashboard, {
        global: {
          plugins: [pinia]
        }
      })

      await nextTick()
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      const activityItems = wrapper.findAll('.activity-item')
      expect(activityItems.length).toBe(3)

      // Each activity should have appropriate icon class
      activities.forEach((activity, index) => {
        const item = activityItems[index]
        const icon = item.find('.activity-icon')
        expect(icon.exists()).toBe(true)
        expect(icon.classes()).toContain(activity.type)
      })
    })
  })

  describe('Activity Response Format Handling', () => {
    it('should handle different API response formats', async () => {
      // Test multiple possible response formats
      const responseFormats = [
        { success: true, data: { activities: [], total_count: 0 } },
        { activities: [] },
        []
      ]

      for (const format of responseFormats) {
        mockApiGet.mockImplementation((url) => {
          if (url.includes('/api/admin/activities')) {
            return Promise.resolve({ data: format })
          }
          return Promise.resolve({ data: {} })
        })

        wrapper = mount(AdminDashboard, {
          global: {
            plugins: [pinia]
          }
        })

        await nextTick()
        await wrapper.vm.$nextTick()
        await new Promise(resolve => setTimeout(resolve, 100))
        await wrapper.vm.$nextTick()

        // Should handle all formats without crashing
        expect(wrapper.find('.recent-activity').exists()).toBe(true)
        
        wrapper.unmount()
      }
    })
  })
})