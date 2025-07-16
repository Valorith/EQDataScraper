/**
 * Backend Discovery Utility
 * Dynamically discovers and validates the backend server URL
 * Provides resilience against port configuration mismatches
 */

// Cache for discovered backend URL
let discoveredBackendUrl = null;
let lastDiscoveryTime = 0;
const DISCOVERY_CACHE_TTL = 5 * 60 * 1000; // 5 minutes
let isDiscovering = false; // Prevent concurrent discoveries
let discoveryPromise = null; // Store ongoing discovery promise

/**
 * Try to fetch config.json to get the configured backend port
 */
async function getConfiguredPort() {
  try {
    const response = await fetch('/config.json');
    if (response.ok) {
      const config = await response.json();
      return config.backend_port || null;
    }
  } catch (error) {
    console.debug('Could not fetch config.json:', error.message);
  }
  return null;
}

/**
 * Check if a backend URL is responding
 */
async function checkBackendHealth(url) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000); // 2 second timeout
    
    const response = await fetch(`${url}/api/health`, {
      signal: controller.signal,
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });
    
    clearTimeout(timeoutId);
    
    if (response.ok) {
      const data = await response.json();
      return data.status === 'healthy';
    }
  } catch (error) {
    // Silently fail - this is expected when trying different ports
  }
  return false;
}

/**
 * Verify if cached backend URL is still responding
 */
async function verifyCachedUrl() {
  if (!discoveredBackendUrl) return false;
  
  try {
    const isHealthy = await checkBackendHealth(discoveredBackendUrl);
    if (!isHealthy) {
      console.debug('Cached backend URL no longer responding, clearing cache');
      clearDiscoveryCache();
    }
    return isHealthy;
  } catch (error) {
    clearDiscoveryCache();
    return false;
  }
}

/**
 * Discover the backend URL by trying multiple strategies
 */
export async function discoverBackendUrl() {
  // Return cached URL if still valid and responding
  if (discoveredBackendUrl && (Date.now() - lastDiscoveryTime) < DISCOVERY_CACHE_TTL) {
    // Quick verification that cached URL still works
    const stillValid = await verifyCachedUrl();
    if (stillValid) {
      return discoveredBackendUrl;
    }
  }
  
  // If already discovering, return the existing promise
  if (isDiscovering && discoveryPromise) {
    return discoveryPromise;
  }
  
  // Start new discovery
  isDiscovering = true;
  discoveryPromise = performDiscovery();
  
  try {
    const result = await discoveryPromise;
    return result;
  } finally {
    isDiscovering = false;
    discoveryPromise = null;
  }
}

/**
 * Perform the actual discovery logic
 */
async function performDiscovery() {
  
  // In production, use the configured URL
  if (import.meta.env.PROD) {
    const envUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_URL;
    if (envUrl && !envUrl.includes('localhost') && !envUrl.includes('127.0.0.1')) {
      discoveredBackendUrl = envUrl;
      lastDiscoveryTime = Date.now();
      return envUrl;
    }
    // Default production URL
    const prodUrl = 'https://eqdatascraper-backend-production.up.railway.app';
    discoveredBackendUrl = prodUrl;
    lastDiscoveryTime = Date.now();
    return prodUrl;
  }
  
  // In development, try multiple strategies
  const candidates = [];
  
  // 1. Try environment variable first
  const envUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_URL;
  if (envUrl) {
    candidates.push(envUrl);
  }
  
  // 2. Try configured port from config.json
  const configuredPort = await getConfiguredPort();
  if (configuredPort) {
    candidates.push(`http://localhost:${configuredPort}`);
  }
  
  // 3. Try common development ports
  const commonPorts = [5002, 5001, 5000, 3001, 8000, 8080];
  for (const port of commonPorts) {
    candidates.push(`http://localhost:${port}`);
  }
  
  // Remove duplicates
  const uniqueCandidates = [...new Set(candidates)];
  
  console.log('🔍 Discovering backend URL...');
  
  // Try each candidate
  for (const url of uniqueCandidates) {
    if (await checkBackendHealth(url)) {
      console.log(`✅ Backend discovered at ${url}`);
      discoveredBackendUrl = url;
      lastDiscoveryTime = Date.now();
      return url;
    }
  }
  
  // If no backend found, return the first candidate as fallback
  console.warn('⚠️ No responsive backend found. Using fallback URL.');
  const fallbackUrl = uniqueCandidates[0] || 'http://localhost:5001';
  // Don't cache failed discovery - retry sooner
  discoveredBackendUrl = null; // Clear cache on failure
  lastDiscoveryTime = 0;
  return fallbackUrl;
}

/**
 * Clear the discovery cache (useful after configuration changes)
 */
export function clearDiscoveryCache() {
  discoveredBackendUrl = null;
  lastDiscoveryTime = 0;
}

/**
 * Get the current discovered backend URL without re-discovering
 */
export function getCurrentBackendUrl() {
  return discoveredBackendUrl;
}