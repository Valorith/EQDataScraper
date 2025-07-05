/**
 * Tests for user authentication store
 */

import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '../userStore'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import axios from 'axios'

// Mock axios
vi.mock('axios')

describe('User Store', () => {
  let store

  beforeEach(() => {
    // Create a fresh pinia instance before each test
    setActivePinia(createPinia())
    store = useUserStore()
    
    // Clear localStorage
    localStorage.clear()
    
    // Reset axios mocks
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      expect(store.user).toBe(null)
      expect(store.accessToken).toBe(null)
      expect(store.refreshToken).toBe(null)
      expect(store.isAuthenticated).toBe(false)
      expect(store.isLoading).toBe(false)
      expect(store.loginError).toBe(null)
      expect(store.preferences).toEqual({
        theme_preference: 'auto',
        results_per_page: 20
      })
    })
  })

  describe('Getters', () => {
    it('should compute fullName correctly', () => {
      // No user
      expect(store.fullName).toBe(null)
      
      // User with full name
      store.user = {
        first_name: 'John',
        last_name: 'Doe',
        email: 'john@example.com'
      }
      expect(store.fullName).toBe('John Doe')
      
      // User with only first name
      store.user = {
        first_name: 'John',
        last_name: '',
        email: 'john@example.com'
      }
      expect(store.fullName).toBe('John')
      
      // User with no name
      store.user = {
        first_name: '',
        last_name: '',
        email: 'john@example.com'
      }
      expect(store.fullName).toBe('john@example.com')
    })

    it('should compute displayName correctly', () => {
      // No user
      expect(store.displayName).toBe(null)
      
      // Anonymous mode without display name
      store.user = {
        anonymous_mode: true,
        display_name: '',
        first_name: 'John',
        last_name: 'Doe',
        email: 'john@example.com'
      }
      expect(store.displayName).toBe('Anonymous User')
      
      // With display name
      store.user = {
        display_name: 'CoolUser123',
        first_name: 'John',
        last_name: 'Doe'
      }
      expect(store.displayName).toBe('CoolUser123')
      
      // No display name, not anonymous
      store.user = {
        display_name: '',
        anonymous_mode: false,
        first_name: 'John',
        last_name: 'Doe'
      }
      expect(store.displayName).toBe('John Doe')
    })

    it('should compute userAvatar correctly', () => {
      // No user
      expect(store.userAvatar).toBe(null)
      
      // Class avatar
      store.user = {
        avatar_class: 'warrior',
        avatar_url: 'https://example.com/photo.jpg'
      }
      expect(store.userAvatar).toEqual({
        type: 'class',
        class: 'warrior',
        url: null
      })
      
      // Google photo avatar
      store.user = {
        avatar_class: null,
        avatar_url: 'https://example.com/photo.jpg'
      }
      expect(store.userAvatar).toEqual({
        type: 'google',
        class: null,
        url: 'https://example.com/photo.jpg'
      })
    })

    it('should return resultsPerPage from preferences', () => {
      expect(store.resultsPerPage).toBe(20)
      
      store.preferences.results_per_page = 50
      expect(store.resultsPerPage).toBe(50)
    })
  })

  describe('Actions', () => {
    describe('initializeFromStorage', () => {
      it('should load auth data from localStorage', () => {
        const mockUser = { id: 1, email: 'test@example.com' }
        const mockPrefs = { theme_preference: 'dark', results_per_page: 50 }
        
        localStorage.setItem('access_token', 'test-access-token')
        localStorage.setItem('refresh_token', 'test-refresh-token')
        localStorage.setItem('user', JSON.stringify(mockUser))
        localStorage.setItem('user_preferences', JSON.stringify(mockPrefs))
        
        store.initializeFromStorage()
        
        expect(store.accessToken).toBe('test-access-token')
        expect(store.refreshToken).toBe('test-refresh-token')
        expect(store.user).toEqual(mockUser)
        expect(store.preferences).toEqual(mockPrefs)
        expect(store.isAuthenticated).toBe(true)
      })

      it('should handle invalid JSON in localStorage', () => {
        localStorage.setItem('user', 'invalid-json')
        localStorage.setItem('user_preferences', 'invalid-json')
        
        // Should not throw
        expect(() => store.initializeFromStorage()).not.toThrow()
        
        expect(store.user).toBe(null)
        expect(store.preferences).toEqual({
          theme_preference: 'auto',
          results_per_page: 20
        })
      })
    })

    describe('handleOAuthCallback', () => {
      it('should handle successful OAuth callback', async () => {
        const mockResponse = {
          data: {
            success: true,
            data: {
              user: { id: 1, email: 'test@example.com' },
              access_token: 'access-123',
              refresh_token: 'refresh-123',
              preferences: { theme_preference: 'dark' }
            }
          }
        }
        
        axios.post.mockResolvedValueOnce(mockResponse)
        
        const result = await store.handleOAuthCallback('test-code', 'test-state', 'test-verifier')
        
        expect(result).toBe(true)
        expect(store.user).toEqual(mockResponse.data.data.user)
        expect(store.accessToken).toBe('access-123')
        expect(store.refreshToken).toBe('refresh-123')
        expect(store.isAuthenticated).toBe(true)
        expect(store.preferences).toEqual({ theme_preference: 'dark' })
        
        // Check localStorage
        expect(localStorage.getItem('access_token')).toBe('access-123')
        expect(localStorage.getItem('user')).toBe(JSON.stringify(mockResponse.data.data.user))
      })

      it('should handle OAuth callback failure', async () => {
        axios.post.mockRejectedValueOnce(new Error('Network error'))
        
        const result = await store.handleOAuthCallback('test-code', 'test-state', 'test-verifier')
        
        expect(result).toBe(false)
        expect(store.loginError).toBe('OAuth callback failed')
        expect(store.isAuthenticated).toBe(false)
      })
    })

    describe('logout', () => {
      it('should clear all auth data', async () => {
        // Set up authenticated state
        store.user = { id: 1, email: 'test@example.com' }
        store.accessToken = 'test-token'
        store.refreshToken = 'test-refresh'
        store.isAuthenticated = true
        
        axios.post.mockResolvedValueOnce({ data: { success: true } })
        
        await store.logout()
        
        // Check store cleared
        expect(store.user).toBe(null)
        expect(store.accessToken).toBe(null)
        expect(store.refreshToken).toBe(null)
        expect(store.isAuthenticated).toBe(false)
        
        // Check localStorage cleared
        expect(localStorage.getItem('access_token')).toBe(null)
        expect(localStorage.getItem('user')).toBe(null)
        
        // Check API called
        expect(axios.post).toHaveBeenCalledWith(
          expect.stringContaining('/api/auth/logout'),
          {},
          expect.objectContaining({
            headers: { Authorization: 'Bearer test-token' }
          })
        )
      })
    })

    describe('updateProfile', () => {
      it('should update user profile', async () => {
        store.accessToken = 'test-token'
        store.user = { id: 1, email: 'test@example.com' }
        
        const updates = {
          display_name: 'NewName',
          anonymous_mode: true,
          avatar_class: 'warrior'
        }
        
        const mockResponse = {
          data: {
            success: true,
            data: {
              user: { ...store.user, ...updates }
            }
          }
        }
        
        axios.put.mockResolvedValueOnce(mockResponse)
        
        await store.updateProfile(updates)
        
        expect(store.user).toEqual(mockResponse.data.data.user)
        expect(axios.put).toHaveBeenCalledWith(
          expect.stringContaining('/api/user/profile'),
          updates,
          expect.objectContaining({
            headers: { Authorization: 'Bearer test-token' }
          })
        )
      })

      it('should validate anonymous mode requires display name', async () => {
        store.user = { id: 1, display_name: '' }
        
        await expect(
          store.updateProfile({ anonymous_mode: true })
        ).rejects.toThrow('Display name is required when anonymous mode is enabled')
      })
    })

    describe('refreshAccessToken', () => {
      it('should refresh access token', async () => {
        store.refreshToken = 'refresh-123'
        
        const mockResponse = {
          data: {
            success: true,
            data: {
              access_token: 'new-access-123'
            }
          }
        }
        
        axios.post.mockResolvedValueOnce(mockResponse)
        
        const result = await store.refreshAccessToken()
        
        expect(result).toBe(true)
        expect(store.accessToken).toBe('new-access-123')
        expect(localStorage.getItem('access_token')).toBe('new-access-123')
      })

      it('should handle refresh failure and logout', async () => {
        store.refreshToken = 'refresh-123'
        store.user = { id: 1 }
        store.isAuthenticated = true
        
        axios.post.mockRejectedValueOnce(new Error('Invalid refresh token'))
        
        const result = await store.refreshAccessToken()
        
        expect(result).toBe(false)
        expect(store.accessToken).toBe(null)
        expect(store.user).toBe(null)
        expect(store.isAuthenticated).toBe(false)
      })
    })
  })
})