/**
 * Utility to clear authentication state
 * Run this in the browser console if you're having OAuth issues
 */

export function clearAuthState() {
  // Clear all auth-related localStorage items
  const authKeys = [
    'user',
    'accessToken', 
    'refreshToken',
    'preferences',
    'oauthState',
    'pinia-user' // Pinia persisted state
  ]
  
  authKeys.forEach(key => {
    localStorage.removeItem(key)
  })
  
  // Clear any keys that contain 'user' or 'auth'
  Object.keys(localStorage).forEach(key => {
    if (key.includes('user') || key.includes('auth') || key.includes('token')) {
      localStorage.removeItem(key)
    }
  })
  
  console.log('✅ Authentication state cleared')
  console.log('🔄 Please refresh the page')
}

// Make it available globally for debugging
if (typeof window !== 'undefined') {
  window.clearAuthState = clearAuthState
}