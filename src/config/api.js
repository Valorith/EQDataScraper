/**
 * Central API configuration
 * This file provides a single source of truth for API URLs
 */

// Determine the API base URL based on environment
export const API_BASE_URL = (() => {
  // Check if we have an explicit backend URL set
  const envBackendUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_URL
  
  // In production mode
  if (import.meta.env.PROD) {
    // Use environment variable if it's a valid production URL (not localhost)
    if (envBackendUrl && !envBackendUrl.includes('localhost') && !envBackendUrl.includes('127.0.0.1')) {
      return envBackendUrl
    }
    // Default production backend URL
    const defaultProdUrl = 'https://eqdatascraper-backend-production.up.railway.app'
    return defaultProdUrl
  }
  
  // In development mode
  if (envBackendUrl) {
    return envBackendUrl
  }
  
  // Default development URL - should match config.json backend_port
  const defaultDevUrl = 'http://localhost:5001'
  return defaultDevUrl
})()

// Export for debugging
export const API_CONFIG = {
  baseUrl: API_BASE_URL,
  isDevelopment: !import.meta.env.PROD,
  isProduction: import.meta.env.PROD,
  environment: import.meta.env.MODE
}

// Helper function to build API endpoints
export function buildApiUrl(endpoint) {
  // Ensure endpoint starts with /
  if (!endpoint.startsWith('/')) {
    endpoint = '/' + endpoint
  }
  return `${API_BASE_URL}${endpoint}`
}

// Common API endpoints
export const API_ENDPOINTS = {
  // Auth endpoints
  AUTH_STATUS: '/api/auth/status',
  AUTH_GOOGLE_LOGIN: '/api/auth/google/login',
  AUTH_GOOGLE_CALLBACK: '/api/auth/google/callback',
  AUTH_REFRESH: '/api/auth/refresh',
  AUTH_LOGOUT: '/api/auth/logout',
  
  // User endpoints
  USER_PROFILE: '/api/user/profile',
  USER_PREFERENCES: '/api/user/preferences',
  
  // Spell endpoints
  CLASSES: '/api/classes',
  SPELLS: (className) => `/api/spells/${className}`,
  SPELL_DETAILS: (spellId) => `/api/spell-details/${spellId}`,
  SEARCH_SPELLS: '/api/search-spells',
  
  // Cache endpoints
  CACHE_STATUS: '/api/cache-status',
  SCRAPE_ALL: '/api/scrape-all',
  REFRESH_SPELL_CACHE: (className) => `/api/refresh-spell-cache/${className}`,
  
  // Admin endpoints
  ADMIN_ACTIVITIES: '/api/admin/activities',
  ADMIN_USERS: '/api/admin/users',
  ADMIN_STATS: '/api/admin/stats',
  ADMIN_CACHE_STATUS: '/api/admin/cache/status',
  ADMIN_CACHE_SAVE: '/api/admin/cache/save',
  ADMIN_CACHE_CLEAR: '/api/admin/cache/clear',
  
  // Health check
  HEALTH: '/api/health'
}

export default API_BASE_URL