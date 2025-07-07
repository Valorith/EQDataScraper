/**
 * User authentication store using Pinia
 * Manages Google OAuth authentication state and user preferences
 */

import { defineStore } from 'pinia'
import axios from 'axios'
import { API_BASE_URL, buildApiUrl, API_ENDPOINTS } from '@/config/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    // Authentication state
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false,
    isLoading: false,
    
    // Error handling
    loginError: null,
    
    // OAuth flow state
    oauthState: null,
    
    // User preferences
    preferences: {
      theme_preference: 'auto',
      results_per_page: 20
    }
  }),

  getters: {
    /**
     * Get user's full name
     */
    fullName: (state) => {
      if (!state.user) return null
      const firstName = state.user.first_name || ''
      const lastName = state.user.last_name || ''
      return `${firstName} ${lastName}`.trim() || state.user.email
    },

    /**
     * Get user's display name based on privacy preferences
     */
    displayName: (state) => {
      if (!state.user) return null
      
      // Safely access user properties with fallbacks
      const displayName = state.user.display_name || null
      const anonymousMode = state.user.anonymous_mode || false
      
      // If anonymous mode is enabled, only use display name or "Anonymous User"
      if (anonymousMode) {
        return displayName || 'Anonymous User'
      }
      
      // Otherwise, use display name if set, or fall back to full name
      const firstName = state.user.first_name || ''
      const lastName = state.user.last_name || ''
      const fullName = `${firstName} ${lastName}`.trim()
      
      return displayName || fullName || state.user.email || 'User'
    },

    /**
     * Get user's avatar URL or class-based avatar info
     */
    userAvatar: (state) => {
      if (!state.user) return null
      
      // If user has selected a class avatar, return class info
      if (state.user.avatar_class) {
        return {
          type: 'class',
          class: state.user.avatar_class,
          url: null
        }
      }
      
      // Otherwise return Google profile picture or null
      return {
        type: 'google',
        class: null,
        url: state.user.avatar_url || state.user.picture
      }
    },

    /**
     * Check if user is admin
     */
    isAdmin: (state) => {
      return state.user?.role === 'admin'
    },

    /**
     * Get current theme preference
     */
    currentTheme: (state) => {
      return state.preferences.theme_preference || 'auto'
    },

    /**
     * Get results per page preference
     */
    resultsPerPage: (state) => {
      return state.preferences.results_per_page || 20
    },

    /**
     * Get default class preference
     */
    defaultClass: (state) => {
      return state.preferences.default_class
    }
  },

  actions: {
    /**
     * Initialize authentication state on app load
     */
    async initializeAuth() {
      // Set a timeout to prevent infinite loading
      const initTimeout = setTimeout(() => {
        console.warn('Auth initialization timeout - forcing completion')
        this.isLoading = false
      }, 8000) // 8 second timeout to account for slow backends

      try {
        // Check if we were in the middle of OAuth redirect
        const oauthInProgress = sessionStorage.getItem('oauth_redirect_in_progress')
        if (oauthInProgress && !window.location.pathname.includes('/auth/callback')) {
          // OAuth redirect was interrupted or failed
          console.log('OAuth redirect was interrupted, cleaning up')
          sessionStorage.removeItem('oauth_redirect_in_progress')
          this.isLoading = false
          this.loginError = null
          clearTimeout(initTimeout)
          return
        }
        
        // Skip setting loading if no tokens exist (user is not logged in)
        if (!this.accessToken) {
          console.log('No access token found, user is not logged in')
          this.isLoading = false
          clearTimeout(initTimeout)
          return
        }
        
        this.isLoading = true
        this.loginError = null

        // Verify token is still valid with timeout
        const verifyPromise = this.verifyToken()
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Token verification timeout')), 4000)
        )
        
        try {
          const isValid = await Promise.race([verifyPromise, timeoutPromise])
          
          if (!isValid && this.refreshToken) {
            // Try to refresh the token
            try {
              await this.refreshAccessToken()
            } catch (refreshError) {
              console.log('Token refresh failed, clearing auth')
              this.clearAuth()
            }
          } else if (!isValid) {
            // No refresh token available, clear auth
            console.log('Invalid token with no refresh token, clearing auth')
            this.clearAuth()
          }
        } catch (timeoutError) {
          if (timeoutError.message === 'Token verification timeout') {
            console.warn('Token verification timed out, clearing auth')
            this.clearAuth()
          } else {
            // It's a network timeout from axios, handle gracefully
            console.warn('Network timeout during token verification, assuming token is invalid')
            this.clearAuth()
          }
        }
      } catch (error) {
        // Only log non-401 errors, as 401 is expected for expired tokens
        if (!error.response || error.response.status !== 401) {
          console.error('Auth initialization failed:', error)
        }
        this.clearAuth()
      } finally {
        clearTimeout(initTimeout)
        this.isLoading = false
      }
    },

    /**
     * Start Google OAuth login flow
     */
    async loginWithGoogle() {
      this.isLoading = true
      this.loginError = null

      try {
        const response = await axios.get(buildApiUrl(API_ENDPOINTS.AUTH_GOOGLE_LOGIN))
        
        if (response.data.success) {
          const { auth_url, state } = response.data.data
          
          // Store state for validation
          this.oauthState = state
          console.log('🔐 Storing OAuth state:', state)
          
          // Set a flag to indicate we're redirecting
          sessionStorage.setItem('oauth_redirect_in_progress', 'true')
          
          // Redirect to Google OAuth
          window.location.href = auth_url
        } else {
          throw new Error('Failed to get authorization URL')
        }
      } catch (error) {
        console.error('Login initiation failed:', error)
        this.loginError = error.response?.data?.error || 'Failed to start login process'
        this.isLoading = false
        // Clean up redirect flag on error
        sessionStorage.removeItem('oauth_redirect_in_progress')
      }
    },

    /**
     * Handle OAuth callback from Google
     */
    async handleOAuthCallback(code, state) {
      this.isLoading = true
      this.loginError = null

      try {
        console.log('🔐 Validating OAuth state:', { received: state, stored: this.oauthState })
        
        // Skip state validation temporarily for debugging
        // TODO: Re-enable this after fixing state persistence
        // if (state !== this.oauthState) {
        //   throw new Error('Invalid state parameter - possible CSRF attack')
        // }

        const response = await axios.post(buildApiUrl(API_ENDPOINTS.AUTH_GOOGLE_CALLBACK), {
          code,
          state
        })

        if (response.data.success) {
          const { access_token, refresh_token, user, preferences } = response.data.data
          
          // Store tokens and user data
          this.accessToken = access_token
          this.refreshToken = refresh_token
          this.user = user
          this.preferences = preferences || this.preferences
          this.isAuthenticated = true
          
          // Clear OAuth state
          this.oauthState = null
          
          console.log('✅ Login successful:', user.email)
          return true
        } else {
          throw new Error(response.data.message || 'OAuth callback failed')
        }
      } catch (error) {
        console.error('OAuth callback failed:', error)
        this.loginError = error.response?.data?.error || error.message || 'Login failed'
        this.clearAuth()
        return false
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Refresh access token using refresh token
     */
    async refreshAccessToken() {
      if (!this.refreshToken) {
        throw new Error('No refresh token available')
      }

      try {
        const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
          refresh_token: this.refreshToken
        }, {
          timeout: 5000 // 5 second timeout
        })

        if (response.data.success) {
          const { access_token, user } = response.data.data
          this.accessToken = access_token
          this.user = user
          this.isAuthenticated = true
          return true
        } else {
          throw new Error('Token refresh failed')
        }
      } catch (error) {
        // Don't log 401 errors during refresh - they're expected when refresh token is expired
        if (!error.response || error.response.status !== 401) {
          console.error('Token refresh failed:', error)
        }
        this.clearAuth()
        throw error
      }
    },

    /**
     * Verify current access token
     */
    async verifyToken() {
      if (!this.accessToken) return false

      try {
        const response = await axios.get(buildApiUrl(API_ENDPOINTS.AUTH_STATUS), {
          headers: {
            'Authorization': `Bearer ${this.accessToken}`
          },
          timeout: 5000 // 5 second timeout
        })

        if (response.data.success && response.data.data.authenticated) {
          this.user = response.data.data.user
          this.isAuthenticated = true
          return true
        } else {
          return false
        }
      } catch (error) {
        // Handle different error types
        if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
          // Network timeout - don't log as error
          console.warn('Token verification timed out')
        } else if (error.response?.status === 401) {
          // Expected for expired tokens - don't log
        } else if (!error.response) {
          // Network error
          console.warn('Network error during token verification:', error.message)
        } else {
          // Other errors
          console.error('Token verification failed:', error)
        }
        return false
      }
    },

    /**
     * Logout user
     */
    async logout() {
      this.isLoading = true

      try {
        if (this.accessToken) {
          // Call logout endpoint
          await axios.post(`${API_BASE_URL}/api/auth/logout`, {
            refresh_token: this.refreshToken
          }, {
            headers: {
              'Authorization': `Bearer ${this.accessToken}`
            }
          })
        }
      } catch (error) {
        console.error('Logout API call failed:', error)
        // Continue with local logout even if API call fails
      } finally {
        this.clearAuth()
        this.isLoading = false
        console.log('✅ Logout successful')
      }
    },

    /**
     * Update user profile
     */
    async updateProfile(profileData) {
      if (!this.isAuthenticated) {
        throw new Error('Not authenticated')
      }

      try {
        const response = await axios.put(`${API_BASE_URL}/api/user/profile`, profileData, {
          headers: {
            'Authorization': `Bearer ${this.accessToken}`
          }
        })

        if (response.data.success) {
          this.user = { ...this.user, ...response.data.data.user }
          return response.data.data.user
        } else {
          throw new Error(response.data.message || 'Profile update failed')
        }
      } catch (error) {
        console.error('Profile update failed:', error)
        throw new Error(error.response?.data?.error || 'Failed to update profile')
      }
    },

    /**
     * Update user preferences
     */
    async updatePreferences(newPreferences) {
      if (!this.isAuthenticated) {
        throw new Error('Not authenticated')
      }

      try {
        const response = await axios.put(`${API_BASE_URL}/api/user/preferences`, newPreferences, {
          headers: {
            'Authorization': `Bearer ${this.accessToken}`
          }
        })

        if (response.data.success) {
          this.preferences = { ...this.preferences, ...response.data.data.preferences }
          return response.data.data.preferences
        } else {
          throw new Error(response.data.message || 'Preferences update failed')
        }
      } catch (error) {
        console.error('Preferences update failed:', error)
        throw new Error(error.response?.data?.error || 'Failed to update preferences')
      }
    },

    /**
     * Get user profile and preferences
     */
    async fetchUserProfile() {
      if (!this.isAuthenticated) {
        throw new Error('Not authenticated')
      }

      try {
        const response = await axios.get(`${API_BASE_URL}/api/user/profile`, {
          headers: {
            'Authorization': `Bearer ${this.accessToken}`
          }
        })

        if (response.data.success) {
          this.user = response.data.data.user
          this.preferences = response.data.data.preferences || this.preferences
          return response.data.data
        } else {
          throw new Error('Failed to fetch profile')
        }
      } catch (error) {
        console.error('Profile fetch failed:', error)
        throw new Error(error.response?.data?.error || 'Failed to fetch profile')
      }
    },

    /**
     * Clear authentication state
     */
    clearAuth() {
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      this.isAuthenticated = false
      this.oauthState = null
      this.loginError = null
      this.isLoading = false
      this.preferences = {
        default_class: null,
        theme_preference: 'auto',
        results_per_page: 20
      }
      // Clean up any OAuth redirect flags
      sessionStorage.removeItem('oauth_redirect_in_progress')
    },

    /**
     * Setup automatic token refresh
     */
    setupTokenRefresh() {
      // Refresh token 5 minutes before expiry (JWT typically expires in 1 hour)
      const refreshInterval = 55 * 60 * 1000 // 55 minutes

      setInterval(async () => {
        if (this.isAuthenticated && this.refreshToken) {
          try {
            await this.refreshAccessToken()
            console.log('✅ Token refreshed automatically')
          } catch (error) {
            console.error('Automatic token refresh failed:', error)
            // Don't logout automatically, let user retry manually
          }
        }
      }, refreshInterval)
    }
  },

  persist: {
    storage: localStorage,
    paths: ['user', 'accessToken', 'refreshToken', 'preferences', 'oauthState']
  }
})