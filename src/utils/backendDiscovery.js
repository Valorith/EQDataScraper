/**
 * Backend Discovery Utility
 * Dynamically discovers and validates the backend server URL
 * Provides resilience against port configuration mismatches
 */

// Cache for discovered backend URL
let discoveredBackendUrl = null;
let lastDiscoveryTime = 0;
const DISCOVERY_CACHE_TTL = 10 * 60 * 1000; // Increased to 10 minutes to reduce health check frequency
let isDiscovering = false; // Prevent concurrent discoveries
let discoveryPromise = null; // Store ongoing discovery promise

// Circuit breaker for health checks to prevent backend overload
let healthCheckFailures = 0;
let lastHealthCheckFailure = 0;
const MAX_HEALTH_CHECK_FAILURES = 5;
const HEALTH_CHECK_COOLDOWN = 2 * 60 * 1000; // 2 minute cooldown after too many failures

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
 * Check if health checks are currently blocked by circuit breaker
 */
function isHealthCheckBlocked() {
  if (healthCheckFailures < MAX_HEALTH_CHECK_FAILURES) {
    return false;
  }
  
  const timeSinceLastFailure = Date.now() - lastHealthCheckFailure;
  if (timeSinceLastFailure > HEALTH_CHECK_COOLDOWN) {
    // Reset circuit breaker after cooldown
    healthCheckFailures = 0;
    lastHealthCheckFailure = 0;
    return false;
  }
  
  return true;
}

/**
 * Record a health check failure for circuit breaker
 */
function recordHealthCheckFailure() {
  healthCheckFailures++;
  lastHealthCheckFailure = Date.now();
  
  if (healthCheckFailures === MAX_HEALTH_CHECK_FAILURES) {
    console.warn(`Health check circuit breaker activated after ${MAX_HEALTH_CHECK_FAILURES} failures. Will retry in ${HEALTH_CHECK_COOLDOWN / 1000}s`);
  }
}

/**
 * Check if a backend URL is responding
 */
async function checkBackendHealth(url) {
  // Circuit breaker: skip health checks if too many recent failures
  if (isHealthCheckBlocked()) {
    console.debug('Health check blocked by circuit breaker');
    return false;
  }
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000); // Increased to 3 second timeout
    
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
      const isHealthy = data.status === 'healthy';
      
      if (isHealthy) {
        // Reset failure count on successful health check
        healthCheckFailures = 0;
        lastHealthCheckFailure = 0;
      }
      
      return isHealthy;
    } else {
      recordHealthCheckFailure();
    }
  } catch (error) {
    recordHealthCheckFailure();
    // Silently fail - this is expected when trying different ports
  }
  return false;
}

/**
 * Verify if cached backend URL is still responding
 */
async function verifyCachedUrl() {
  if (!discoveredBackendUrl) return false;
  
  // Skip verification if health checks are blocked by circuit breaker
  if (isHealthCheckBlocked()) {
    console.debug('Skipping cached URL verification due to circuit breaker');
    return true; // Assume it's still good if we can't check
  }
  
  try {
    const isHealthy = await checkBackendHealth(discoveredBackendUrl);
    if (!isHealthy) {
      console.debug('Cached backend URL no longer responding, clearing cache');
      clearDiscoveryCache();
    }
    return isHealthy;
  } catch (error) {
    console.debug('Error verifying cached URL:', error.message);
    // Don't clear cache on error - might be temporary network issue
    return true; // Keep using cached URL if verification fails
  }
}

/**
 * Discover the backend URL by trying multiple strategies
 */
export async function discoverBackendUrl() {
  // Return cached URL if still valid and not expired
  if (discoveredBackendUrl && (Date.now() - lastDiscoveryTime) < DISCOVERY_CACHE_TTL) {
    // Only verify cached URL occasionally to reduce health check load
    const cacheAge = Date.now() - lastDiscoveryTime;
    const shouldVerify = cacheAge > (DISCOVERY_CACHE_TTL / 2); // Verify only after half the TTL
    
    if (!shouldVerify) {
      return discoveredBackendUrl;
    }
    
    // Quick verification that cached URL still works
    const stillValid = await verifyCachedUrl();
    if (stillValid) {
      return discoveredBackendUrl;
    }
  }
  
  // Skip discovery if health checks are blocked by circuit breaker
  if (isHealthCheckBlocked()) {
    console.debug('Discovery blocked by health check circuit breaker');
    return discoveredBackendUrl || 'http://localhost:5001'; // Return cached or fallback
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