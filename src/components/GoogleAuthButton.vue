<template>
  <div class="google-auth-container">
    <button 
      @click="handleLogin"
      :disabled="isLoading"
      class="google-auth-button"
      :class="{ 'loading': isLoading }"
    >
      <div class="button-content">
        <svg v-if="!isLoading" class="google-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
        </svg>
        
        <div v-if="isLoading" class="loading-spinner"></div>
        
        <span class="button-text">
          {{ isLoading ? 'Signing in...' : 'Sign in with Google' }}
        </span>
      </div>
    </button>
    
    <div v-if="errorMessage" class="error-message">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script>
import { useUserStore } from '@/stores/userStore'
import { computed, onMounted, ref, watch } from 'vue'

export default {
  name: 'GoogleAuthButton',
  emits: ['trigger-dev-login'],
  setup(props, { emit }) {
    const userStore = useUserStore()
    const localLoading = ref(false)
    const loadingTimeout = ref(null)

    const isLoading = computed(() => localLoading.value || userStore.isLoading)
    const errorMessage = computed(() => userStore.loginError)

    const handleLogin = async () => {
      // Prevent multiple clicks
      if (localLoading.value || userStore.isLoading) {
        return
      }
      
      // Check custom app mode from run.py (development vs production)
      const appMode = import.meta.env.VITE_APP_MODE || 'undefined'
      console.log('🔐 GoogleAuthButton: Sign in initiated')
      console.log(`🔧 App Mode: ${appMode} (set by run.py ${appMode === 'development' ? 'start dev' : 'start'})`)
      
      if (appMode === 'development') {
        console.log('🛠️  Development mode detected - checking if dev auth bypass is enabled...')
        
        // Do a fresh check for dev mode (avoid relying on cached state)
        try {
          // Import axios and API config here to avoid circular dependencies
          const axios = (await import('axios')).default
          const { getOAuthApiBaseUrl } = await import('@/config/api')
          const apiBaseUrl = getOAuthApiBaseUrl()
          
          console.log(`🌐 Checking dev auth status at: ${apiBaseUrl}/api/auth/dev-status`)
          
          const response = await axios.get(`${apiBaseUrl}/api/auth/dev-status`, {
            timeout: 3000
          })
          
          const devModeEnabled = response.data.dev_auth_enabled || false
          console.log(`✅ Dev auth status response: ${devModeEnabled}`)
          
          // If dev mode is enabled, trigger dev login panel
          if (devModeEnabled) {
            console.log('🔧 Dev auth bypass enabled → Opening dev login panel')
            emit('trigger-dev-login')
            return
          } else {
            console.log('🏭 Dev auth bypass disabled → Proceeding with Google OAuth')
          }
        } catch (error) {
          console.warn('⚠️  Dev auth check failed → Falling back to Google OAuth')
          console.warn(`   Error: ${error.message}`)
          console.warn('   This is normal if backend is not running or dev auth is disabled')
          // If dev check fails, proceed with normal Google OAuth
        }
      } else {
        console.log('🏭 Production mode detected → Proceeding directly with Google OAuth')
        console.log('   (Dev auth checks are disabled in production mode)')
      }
      
      localLoading.value = true
      
      // Set a timeout to reset loading state if something goes wrong
      loadingTimeout.value = setTimeout(() => {
        localLoading.value = false
        userStore.isLoading = false
        console.warn('Login timeout - resetting loading state')
      }, 10000) // 10 second timeout
      
      try {
        await userStore.loginWithGoogle()
        // The page will redirect, so we don't need to reset loading here
      } catch (error) {
        console.error('Login failed:', error)
        localLoading.value = false
        clearTimeout(loadingTimeout.value)
      }
    }
    
    // Watch for userStore loading changes
    watch(() => userStore.isLoading, (newVal) => {
      if (!newVal && loadingTimeout.value) {
        clearTimeout(loadingTimeout.value)
        localLoading.value = false
      }
    })
    
    // Reset loading state on mount (in case of race condition)
    onMounted(() => {
      // Add a small delay to ensure App.vue initialization has started
      setTimeout(() => {
        // If we're not on the callback page and loading is stuck, reset it
        if (!window.location.pathname.includes('/auth/callback')) {
          // Only reset if loading has been stuck for more than reasonable time
          // and user is not authenticated
          if (userStore.isLoading && !userStore.isAuthenticated && !localLoading.value) {
            console.log('Detected stuck loading state in GoogleAuthButton')
            // Don't immediately reset - give it a moment more
            setTimeout(() => {
              if (userStore.isLoading && !userStore.isAuthenticated) {
                console.log('Force resetting stuck loading state')
                userStore.isLoading = false
              }
            }, 2000)
          }
          localLoading.value = false
        }
      }, 100) // Small delay to avoid race with App.vue initialization
    })

    return {
      handleLogin,
      isLoading,
      errorMessage
    }
  }
}
</script>

<style scoped>
.google-auth-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.google-auth-button {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  padding: 10px 20px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(20px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  min-width: 160px;
  position: relative;
}

.google-auth-button:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.google-auth-button:active:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.google-auth-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.google-auth-button.loading {
  pointer-events: none;
}

.button-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.google-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  filter: brightness(0) invert(1);
  opacity: 0.9;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.button-text {
  white-space: nowrap;
  font-weight: 500;
  letter-spacing: 0.25px;
}

.error-message {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  padding: 12px 16px;
  color: #fca5a5;
  font-size: 14px;
  text-align: center;
  max-width: 300px;
  word-wrap: break-word;
  backdrop-filter: blur(10px);
}

/* Remove dark mode overrides - we want consistent glassmorphism */

/* Adjust button content spacing for better visual balance */
.button-content {
  gap: 10px;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .google-auth-button {
    min-width: 140px;
    padding: 8px 16px;
    font-size: 13px;
  }
  
  .google-icon {
    width: 16px;
    height: 16px;
  }
  
  .loading-spinner {
    width: 16px;
    height: 16px;
  }
}
</style>