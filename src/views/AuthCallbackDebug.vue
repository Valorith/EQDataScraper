<template>
  <div class="auth-callback-container">
    <div class="auth-callback-content">
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner"></div>
        <h2>Debugging OAuth callback...</h2>
        <p>Using enhanced diagnostic endpoint to identify issues.</p>
      </div>

      <div v-else-if="error" class="error-state">
        <div class="error-icon">⚠️</div>
        <h2>OAuth Debug Results</h2>
        <div class="debug-info">
          <h3>Error Details:</h3>
          <pre class="error-details">{{ error }}</pre>
          
          <h3>Debug Information:</h3>
          <pre class="debug-details">{{ debugInfo }}</pre>
        </div>
        <div class="error-actions">
          <router-link to="/" class="btn btn-primary">Return Home</router-link>
          <button @click="retryLogin" class="btn btn-secondary">Try Again</button>
          <button @click="copyDebugInfo" class="btn btn-tertiary">Copy Debug Info</button>
        </div>
      </div>

      <div v-else-if="success" class="success-state">
        <div class="success-icon">✅</div>
        <h2>OAuth Debug Successful!</h2>
        <p>The enhanced callback worked correctly.</p>
        <div class="debug-info">
          <h3>Success Details:</h3>
          <pre class="success-details">{{ JSON.stringify(successData, null, 2) }}</pre>
        </div>
        <div class="success-actions">
          <router-link to="/" class="btn btn-primary">Continue to App</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { API_BASE_URL } from '@/config/api'

export default {
  name: 'AuthCallbackDebug',
  setup() {
    const route = useRoute()
    const router = useRouter()

    const isLoading = ref(true)
    const error = ref(null)
    const success = ref(false)
    const debugInfo = ref({})
    const successData = ref(null)

    const handleDebugCallback = async () => {
      try {
        // Get query parameters from URL
        const code = route.query.code
        const state = route.query.state
        const errorParam = route.query.error

        // Log initial debug info
        debugInfo.value = {
          receivedParams: {
            code: !!code,
            state: !!state,
            error: errorParam
          },
          url: window.location.href,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent
        }

        console.log('🔧 Debug OAuth callback starting...', debugInfo.value)

        // Check for OAuth errors
        if (errorParam) {
          throw new Error(`OAuth error from Google: ${errorParam}`)
        }

        // Validate required parameters
        if (!code) {
          throw new Error('Missing authorization code from Google')
        }

        if (!state) {
          throw new Error('Missing state parameter - possible security issue')
        }

        // Use the enhanced callback endpoint
        const backendUrl = API_BASE_URL || (import.meta.env.PROD ? 'https://eqdatascraper-backend-production.up.railway.app' : '')
        const callbackUrl = `${backendUrl}/api/auth/google/callback-enhanced`
        
        console.log('🔧 Calling enhanced callback:', callbackUrl)

        const response = await axios.post(callbackUrl, {
          code,
          state
        })

        if (response.data.success) {
          console.log('✅ Enhanced OAuth callback successful')
          success.value = true
          successData.value = response.data.data
        } else {
          throw new Error(response.data.message || 'Enhanced OAuth callback failed')
        }

      } catch (err) {
        console.error('🚨 Enhanced OAuth callback error:', err)
        error.value = err.message || 'An unexpected error occurred during sign in'
        
        // Capture more debug info on error
        debugInfo.value = {
          ...debugInfo.value,
          error: {
            message: err.message,
            response: err.response?.data,
            status: err.response?.status,
            stack: err.stack
          }
        }
      } finally {
        isLoading.value = false
      }
    }

    const retryLogin = () => {
      // Go back to home and try login again
      router.push('/')
    }

    const copyDebugInfo = async () => {
      const debugText = JSON.stringify({
        error: error.value,
        debugInfo: debugInfo.value,
        timestamp: new Date().toISOString()
      }, null, 2)
      
      try {
        await navigator.clipboard.writeText(debugText)
        console.log('✅ Debug info copied to clipboard')
      } catch (err) {
        console.error('❌ Failed to copy debug info:', err)
        // Fallback
        const textArea = document.createElement('textarea')
        textArea.value = debugText
        document.body.appendChild(textArea)
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
      }
    }

    onMounted(() => {
      // Small delay to show loading state
      setTimeout(handleDebugCallback, 500)
    })

    return {
      isLoading,
      error,
      success,
      debugInfo,
      successData,
      retryLogin,
      copyDebugInfo,
      JSON
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
  max-width: 800px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.debug-info {
  text-align: left;
  margin: 20px 0;
}

.debug-info h3 {
  color: #2d3748;
  margin: 16px 0 8px 0;
  font-size: 16px;
}

.error-details,
.debug-details,
.success-details {
  background: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  font-family: monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 300px;
  overflow-y: auto;
  color: #2d3748;
}

.error-details {
  background: #fed7d7;
  border-color: #feb2b2;
  color: #c53030;
}

.success-details {
  background: #c6f6d5;
  border-color: #9ae6b4;
  color: #22543d;
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

.btn-tertiary {
  background: #ed8936;
  color: white;
}

.btn-tertiary:hover {
  background: #dd6b20;
  transform: translateY(-1px);
}

/* Mobile responsive */
@media (max-width: 768px) {
  .auth-callback-content {
    padding: 32px 24px;
    margin: 16px;
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
  
  .debug-details,
  .error-details,
  .success-details {
    font-size: 11px;
  }
}
</style>