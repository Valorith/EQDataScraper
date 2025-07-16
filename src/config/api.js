/**
 * Central API configuration
 * This file provides a single source of truth for API URLs
 */

import { discoverBackendUrl, getCurrentBackendUrl } from '../utils/backendDiscovery'

// Initialize with a temporary URL - will be updated by discovery
let API_BASE_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_URL || 'http://localhost:5001'

// In production, use fixed URL immediately
if (import.meta.env.PROD) {
  const envBackendUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_URL
  if (envBackendUrl && !envBackendUrl.includes('localhost') && !envBackendUrl.includes('127.0.0.1')) {
    API_BASE_URL = envBackendUrl
  } else {
    API_BASE_URL = 'https://eqdatascraper-backend-production.up.railway.app'
  }
} else {
  // In development, start discovery process but don't spam console
  discoverBackendUrl().then(url => {
    API_BASE_URL = url
    console.log('🔌 API Base URL set to:', API_BASE_URL)
  }).catch(error => {
    // Silent fail - backend discovery will retry automatically
    console.debug('Initial backend discovery failed, will retry automatically')
  })
}

// Export a getter function to always get the current URL
export function getApiBaseUrl() {
  // If we have a discovered URL, use it
  const discovered = getCurrentBackendUrl()
  if (discovered) {
    return discovered
  }
  return API_BASE_URL
}

// For backward compatibility, export the initial URL
export { API_BASE_URL }

// Export for debugging
export const API_CONFIG = {
  get baseUrl() { return getApiBaseUrl() },
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
  // Use the dynamic getter to always get current URL
  return `${getApiBaseUrl()}${endpoint}`
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
  
  // Spell endpoints - DISABLED
  // Note: Spell system temporarily disabled for redesign
  
  // Admin endpoints
  ADMIN_ACTIVITIES: '/api/admin/activities',
  ADMIN_USERS: '/api/admin/users',
  ADMIN_STATS: '/api/admin/stats',
  
  // Health check
  HEALTH: '/api/health'
}

export default API_BASE_URL