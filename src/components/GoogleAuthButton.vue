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
import { computed } from 'vue'

export default {
  name: 'GoogleAuthButton',
  setup() {
    const userStore = useUserStore()

    const isLoading = computed(() => userStore.isLoading)
    const errorMessage = computed(() => userStore.loginError)

    const handleLogin = async () => {
      try {
        await userStore.loginWithGoogle()
      } catch (error) {
        console.error('Login failed:', error)
      }
    }

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