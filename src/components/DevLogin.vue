<template>
  <div class="dev-login-container" :class="{ minimized: isMinimized }">
    <!-- Minimized state - clickable icon -->
    <div v-if="isMinimized" class="minimized-icon" @click="toggleMinimize" title="Open Dev Login">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M10 17L15 12L10 7V17Z" fill="currentColor"/>
        <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
      </svg>
      <div class="dev-badge">DEV</div>
    </div>
    
    <!-- Expanded state -->
    <div v-else class="expanded-panel">
      <div class="dev-warning">
        <span class="warning-icon">⚠️</span>
        <span>Development Mode - Auth Bypass Active</span>
        <button class="minimize-btn" @click="toggleMinimize" title="Minimize">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 15L12 8L19 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
      
      <div class="dev-login-panel">
      <h3>Quick Dev Login</h3>
      <p class="dev-info">Skip OAuth for local development</p>
      
      <div class="dev-login-options">
        <button @click="loginAsUser" class="dev-login-btn user-btn">
          <span class="icon">👤</span>
          Login as Test User
        </button>
        
        <button @click="loginAsAdmin" class="dev-login-btn admin-btn">
          <span class="icon">👨‍💼</span>
          Login as Admin
        </button>
        
        <button @click="loginCustom" class="dev-login-btn custom-btn">
          <span class="icon">⚙️</span>
          Custom User
        </button>
      </div>
      
      <div v-if="showCustomForm" class="custom-form">
        <input 
          v-model="customEmail" 
          type="email" 
          placeholder="test@example.com"
          class="custom-input"
        >
        <label class="admin-checkbox">
          <input v-model="customIsAdmin" type="checkbox">
          Admin privileges
        </label>
        <button @click="submitCustomLogin" class="submit-btn">Login</button>
      </div>
      
      <div v-if="error" class="error-msg">{{ error }}</div>
    </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watchEffect } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { useRouter } from 'vue-router'
import { useDevMode } from '@/composables/useDevMode'
import axios from 'axios'
import { getOAuthApiBaseUrl } from '@/config/api'

export default {
  name: 'DevLogin',
  props: {},
  setup(props) {
    const userStore = useUserStore()
    const router = useRouter()
    
    // Use shared dev mode state
    const { isDevAuthEnabled } = useDevMode()
    
    const isProduction = import.meta.env.PROD
    const isMinimized = ref(true) // Start minimized
    const showCustomForm = ref(false)
    const customEmail = ref('')
    const customIsAdmin = ref(false)
    const error = ref(null)
    
    // Watch for authentication state changes and save dev login state
    watchEffect(() => {
      if (userStore.isAuthenticated) {
        userStore.saveDevLoginState()
      }
    })
    
    // Computed property to determine if we should show the dev login
    const showDevLogin = computed(() => {
      // Check custom app mode from run.py
      const appMode = import.meta.env.VITE_APP_MODE
      if (appMode !== 'development') return false
      
      // Show dev login if dev auth is enabled (useDevMode handles all fallback logic)
      return isDevAuthEnabled.value
    })
    
    // Watch for changes in dev auth status for debugging
    watchEffect(() => {
      console.debug('DevLogin: Dev auth enabled:', isDevAuthEnabled.value, 'Show:', showDevLogin.value)
    })
    
    const performOfflineLogin = (email, isAdmin = false) => {
      console.log(`🔧 Dev Login: Using offline fallback login for ${email} (admin: ${isAdmin})`)
      
      // Create mock authentication state
      const mockUser = {
        id: isAdmin ? 1 : 2,
        email: email,
        first_name: isAdmin ? 'Admin' : 'Test',
        last_name: 'User',
        role: isAdmin ? 'admin' : 'user',
        display_name: null,
        anonymous_mode: false,
        avatar_class: null,
        avatar_url: `https://ui-avatars.com/api/?name=${isAdmin ? 'Admin' : 'Test'}+User&background=667eea&color=fff`,
        is_active: true,
        google_id: `offline_${isAdmin ? 'admin' : 'user'}`
      }
      
      // Create mock tokens
      const mockAccessToken = `offline_access_token_${Date.now()}`
      const mockRefreshToken = `offline_refresh_token_${Date.now()}`
      
      // Store auth data
      userStore.accessToken = mockAccessToken
      userStore.refreshToken = mockRefreshToken
      userStore.user = mockUser
      userStore.preferences = {
        default_class: null,
        theme_preference: 'auto',
        results_per_page: 20
      }
      userStore.isAuthenticated = true
      
      // Save dev login state for hot reload persistence
      userStore.saveDevLoginState()
      
      // Hide the dev login panel after successful login
      isMinimized.value = true
      showCustomForm.value = false
      
      console.log('🔧 Dev Login: Offline authentication complete, redirecting to home')
      
      // Redirect to home
      router.push('/')
      
      // Clear any previous errors
      error.value = null
    }
    
    const performDevLogin = async (email, isAdmin = false) => {
      error.value = null
      console.log(`🔧 Dev Login: Attempting login for ${email} (admin: ${isAdmin})`)
      const apiBaseUrl = getOAuthApiBaseUrl()
      console.log(`🔧 Dev Login: Using API URL: ${apiBaseUrl}/api/auth/dev-login`)
      
      // If this is a retry after an error and we're in dev mode, use offline login
      if (error.value && error.value.includes('Click again to use offline dev login')) {
        performOfflineLogin(email, isAdmin)
        return
      }
      
      try {
        const response = await axios.post(`${apiBaseUrl}/api/auth/dev-login`, {
          email,
          is_admin: isAdmin
        }, {
          timeout: 10000 // Reduced timeout to 10 seconds for faster fallback
        })
        
        console.log('🔧 Dev Login: Response received', response.data)
        
        if (response.data.success) {
          const { access_token, refresh_token, user, preferences } = response.data.data
          
          console.log('🔧 Dev Login: Login successful, storing auth data')
          
          // Store auth data
          userStore.accessToken = access_token
          userStore.refreshToken = refresh_token
          userStore.user = {
            ...user,
            display_name: user.display_name || null,
            anonymous_mode: user.anonymous_mode || false,
            avatar_class: user.avatar_class || null,
            picture: user.avatar_url || null
          }
          userStore.preferences = preferences || userStore.preferences
          userStore.isAuthenticated = true
          
          // Save dev login state for hot reload persistence
          userStore.saveDevLoginState()
          
          // Hide the dev login panel after successful login
          isMinimized.value = true
          showCustomForm.value = false
          
          console.log('🔧 Dev Login: Authentication complete, redirecting to home')
          
          // Redirect to home
          router.push('/')
        } else {
          console.error('🔧 Dev Login: Backend returned success=false')
          error.value = response.data.message || 'Dev login failed'
        }
      } catch (err) {
        console.error('🔧 Dev Login: Error occurred', err)
        
        // Auto-fallback to offline login for common backend issues
        const shouldAutoFallback = import.meta.env.MODE === 'development' && (
          err.code === 'ECONNABORTED' || 
          err.message.includes('timeout') ||
          err.code === 'ECONNREFUSED' ||
          err.response?.status === 500 ||
          err.response?.status === 404
        )
        
        if (shouldAutoFallback) {
          console.log('🔧 Dev Login: Backend unavailable, auto-falling back to offline login')
          performOfflineLogin(email, isAdmin)
          return
        }
        
        // Set error messages for other failures
        if (err.code === 'ECONNABORTED' || err.message.includes('timeout')) {
          error.value = 'Dev login timed out - using offline fallback'
        } else if (err.response?.status === 404) {
          error.value = 'Dev login endpoint not found - using offline fallback'
        } else if (err.response?.status === 500) {
          error.value = 'Backend error during dev login - using offline fallback'
        } else if (err.code === 'ECONNREFUSED') {
          error.value = 'Cannot connect to backend - using offline fallback'
        } else {
          error.value = err.response?.data?.error || err.message || 'Dev login failed'
        }
        
        // If we didn't auto-fallback, still offer manual fallback
        if (!shouldAutoFallback && import.meta.env.MODE === 'development') {
          console.log('🔧 Dev Login: Offering manual offline fallback login')
          setTimeout(() => {
            error.value += ' - Click again to use offline dev login'
          }, 1000)
        }
      }
    }
    
    const loginAsUser = () => performDevLogin('testuser@localhost.dev', false)
    const loginAsAdmin = () => performDevLogin('admin@localhost.dev', true)
    
    const loginCustom = () => {
      showCustomForm.value = !showCustomForm.value
      customEmail.value = ''
      customIsAdmin.value = false
    }
    
    const submitCustomLogin = () => {
      if (!customEmail.value) {
        error.value = 'Please enter an email'
        return
      }
      performDevLogin(customEmail.value, customIsAdmin.value)
    }
    
    const toggleMinimize = () => {
      // Don't do anything in production or if not in dev mode
      if (isProduction || !showDevLogin.value) {
        console.debug('DevLogin: Toggle ignored - not in dev mode')
        return
      }
      
      isMinimized.value = !isMinimized.value
      // Reset custom form when minimizing
      if (isMinimized.value) {
        showCustomForm.value = false
        error.value = null
      }
    }
    
    
    return {
      isProduction,
      isDevAuthEnabled,
      isMinimized,
      showDevLogin,
      showCustomForm,
      customEmail,
      customIsAdmin,
      error,
      loginAsUser,
      loginAsAdmin,
      loginCustom,
      submitCustomLogin,
      toggleMinimize
    }
  }
}
</script>

<style scoped>
.dev-login-container {
  position: fixed;
  bottom: 80px !important; /* Position at same level as debug panel when expanded */
  right: 20px !important; /* Default right position */
  z-index: 10000; /* Higher than cache indicator */
  max-width: 300px;
  transition: all 0.3s ease;
}

/* When minimized, position at button level next to debug toggle */
.dev-login-container.minimized {
  bottom: 20px !important; /* Same level as debug toggle button */
  right: 20px !important; /* Position at right edge, to the right of debug toggle button */
}



.dev-login-container:not(.minimized) {
  width: 300px;
}

/* Minimized state - small icon */
.minimized-icon {
  background: rgba(26, 32, 44, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
}

.minimized-icon:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.4);
  background: rgba(26, 32, 44, 0.98);
}

.minimized-icon svg {
  color: #48bb78;
  width: 20px;
  height: 20px;
}

.dev-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  background: #ff6b6b;
  color: white;
  font-size: 8px;
  font-weight: 700;
  padding: 2px 4px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.dev-warning {
  background: #ff6b6b;
  color: white;
  padding: 8px 12px;
  border-radius: 4px 4px 0 0;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}

.warning-icon {
  font-size: 14px;
}

.minimize-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 2px;
  border-radius: 2px;
  margin-left: auto;
  transition: background-color 0.2s;
}

.minimize-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.dev-login-panel {
  background: rgba(26, 32, 44, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0 0 8px 8px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.dev-login-panel h3 {
  color: #f7fafc;
  margin: 0 0 4px 0;
  font-size: 16px;
}

.dev-info {
  color: #a0aec0;
  font-size: 12px;
  margin: 0 0 12px 0;
}

.dev-login-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dev-login-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #e2e8f0;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.dev-login-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-1px);
}

.dev-login-btn .icon {
  font-size: 16px;
}

.user-btn:hover {
  border-color: #4299e1;
}

.admin-btn:hover {
  border-color: #f56565;
}

.custom-btn:hover {
  border-color: #48bb78;
}

.custom-form {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.custom-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #e2e8f0;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 13px;
  margin-bottom: 8px;
}

.custom-input::placeholder {
  color: #718096;
}

.admin-checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #a0aec0;
  font-size: 12px;
  margin-bottom: 8px;
}

.submit-btn {
  background: #4299e1;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  width: 100%;
  transition: background 0.2s;
}

.submit-btn:hover {
  background: #3182ce;
}

.error-msg {
  background: rgba(245, 101, 101, 0.1);
  border: 1px solid rgba(245, 101, 101, 0.3);
  color: #fc8181;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 12px;
  margin-top: 8px;
}

/* Hide in production builds */
@media (min-width: 0px) {
  .dev-login-container[data-env="production"] {
    display: none !important;
  }
}

/* Mobile responsive positioning */
@media (max-width: 768px) {
  .dev-login-container {
    bottom: 70px; /* Adjust for mobile when expanded */
    right: 10px;
  }
  
  .dev-login-container.minimized {
    bottom: 10px; /* Adjust for mobile when minimized */
    right: 10px;
  }
  
}
</style>