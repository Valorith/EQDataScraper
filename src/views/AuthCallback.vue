<template>
  <div class="auth-callback-container">
    <div class="auth-callback-content">
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner"></div>
        <h2>Completing sign in...</h2>
        <p>Please wait while we verify your Google account.</p>
      </div>

      <div v-else-if="error" class="error-state">
        <div class="error-icon">⚠️</div>
        <h2>Sign in failed</h2>
        <p class="error-message">{{ error }}</p>
        <div class="error-actions">
          <router-link to="/" class="btn btn-primary">Return Home</router-link>
          <button @click="retryLogin" class="btn btn-secondary">Try Again</button>
        </div>
      </div>

      <div v-else-if="success" class="success-state">
        <div class="success-icon">✅</div>
        <h2>Welcome {{ userName }}!</h2>
        <p>You've successfully signed in to EQDataScraper.</p>
        <div class="success-actions">
          <router-link to="/" class="btn btn-primary">Continue to App</router-link>
          <router-link to="/profile" class="btn btn-secondary">View Profile</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'

export default {
  name: 'AuthCallback',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const userStore = useUserStore()

    const isLoading = ref(true)
    const error = ref(null)
    const success = ref(false)

    const userName = computed(() => {
      return userStore.fullName || userStore.user?.email || 'User'
    })

    const handleCallback = async () => {
      try {
        // Clean up OAuth redirect flag immediately
        sessionStorage.removeItem('oauth_redirect_in_progress')
        
        // Get query parameters from URL
        const code = route.query.code
        const state = route.query.state
        const errorParam = route.query.error

        // Check for OAuth errors
        if (errorParam) {
          throw new Error(`OAuth error: ${errorParam}`)
        }

        // Validate required parameters
        if (!code) {
          throw new Error('Missing authorization code from Google')
        }

        if (!state) {
          throw new Error('Missing state parameter - possible security issue')
        }

        console.log('Processing OAuth callback...', { code: !!code, state: !!state })

        // Handle the OAuth callback
        const callbackResult = await userStore.handleOAuthCallback(code, state)

        if (callbackResult) {
          console.log('✅ OAuth callback successful')
          success.value = true
          
          // Redirect to home page after a short delay
          setTimeout(() => {
            router.push('/')
          }, 2000)
        } else {
          throw new Error('OAuth callback failed')
        }

      } catch (err) {
        console.error('OAuth callback error:', err)
        error.value = err.message || 'An unexpected error occurred during sign in'
        // Ensure userStore loading state is reset on error
        userStore.isLoading = false
      } finally {
        isLoading.value = false
      }
    }

    const retryLogin = () => {
      // Clear any existing auth state and retry
      userStore.clearAuth()
      userStore.loginWithGoogle()
    }

    onMounted(() => {
      // Small delay to show loading state
      setTimeout(handleCallback, 500)
    })

    return {
      isLoading,
      error,
      success,
      userName,
      retryLogin
    }
  }
}
</script>

<style scoped>
.auth-callback-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.auth-callback-content {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 48px;
  text-align: center;
  max-width: 480px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.loading-state,
.error-state,
.success-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 8px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon,
.success-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

h2 {
  color: #2d3748;
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

p {
  color: #4a5568;
  font-size: 16px;
  line-height: 1.5;
  margin: 0;
}

.error-message {
  background: #fed7d7;
  color: #c53030;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #feb2b2;
  font-size: 14px;
  margin: 8px 0;
}

.error-actions,
.success-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  flex-wrap: wrap;
  justify-content: center;
}

.btn {
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  border: none;
  font-size: 14px;
  transition: all 0.2s ease;
  display: inline-block;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover {
  background: #5a67d8;
  transform: translateY(-1px);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.8);
  color: #4a5568;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.95);
  transform: translateY(-1px);
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .auth-callback-content {
    background: rgba(26, 32, 44, 0.95);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  h2 {
    color: #f7fafc;
  }
  
  p {
    color: #e2e8f0;
  }
  
  .btn-secondary {
    background: rgba(45, 55, 72, 0.8);
    color: #e2e8f0;
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .btn-secondary:hover {
    background: rgba(45, 55, 72, 0.95);
  }
}

/* Mobile responsive */
@media (max-width: 768px) {
  .auth-callback-content {
    padding: 32px 24px;
    margin: 16px;
  }
  
  h2 {
    font-size: 20px;
  }
  
  p {
    font-size: 14px;
  }
  
  .error-actions,
  .success-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  .btn {
    width: 100%;
    padding: 14px 24px;
  }
}

/* Animation for state transitions */
.loading-state,
.error-state,
.success-state {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>