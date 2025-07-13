#!/usr/bin/env node

/**
 * Production Debugging Script for EQDataScraper
 * 
 * This script provides comprehensive debugging for production issues,
 * specifically focusing on Railway deployment problems.
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');

// ANSI color codes for better console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m'
};

// Helper function to log with colors
function log(message, color = 'white') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logHeader(title) {
  log('\n' + '='.repeat(80), 'cyan');
  log(title.toUpperCase(), 'bright');
  log('='.repeat(80), 'cyan');
}

function logSection(title) {
  log('\n' + '-'.repeat(40), 'yellow');
  log(title, 'yellow');
  log('-'.repeat(40), 'yellow');
}

function logError(message) {
  log(`❌ ${message}`, 'red');
}

function logSuccess(message) {
  log(`✅ ${message}`, 'green');
}

function logWarning(message) {
  log(`⚠️  ${message}`, 'yellow');
}

function logInfo(message) {
  log(`ℹ️  ${message}`, 'blue');
}

// Configuration
const CONFIG = {
  // Frontend URLs
  FRONTEND_PROD: 'https://eqdatascraper-production.up.railway.app',
  FRONTEND_LOCAL: 'http://localhost:3000',
  
  // Backend URLs
  BACKEND_PROD: 'https://eqdatascraper-backend-production.up.railway.app',
  BACKEND_LOCAL: 'http://localhost:5001',
  
  // Build paths
  BUILD_DIR: './dist',
  PACKAGE_JSON: './package.json',
  VITE_CONFIG: './vite.config.js',
  
  // Test endpoints
  TEST_ENDPOINTS: [
    '/api/health',
    '/api/classes',
    '/api/cache-status'
  ],
  
  // Environment files
  ENV_FILES: ['.env', '.env.local', '.env.production']
};

class ProductionDebugger {
  constructor() {
    this.issues = [];
    this.recommendations = [];
  }

  async runAllChecks() {
    logHeader('Production Debugging - EQDataScraper');
    
    try {
      await this.checkEnvironmentVariables();
      await this.checkBuildOutput();
      await this.checkNetworkConnectivity();
      await this.checkBackendAPI();
      await this.checkFrontendBuild();
      await this.checkRailwayConfiguration();
      await this.performEndToEndTest();
      
      this.printSummary();
      
    } catch (error) {
      logError(`Critical error during debugging: ${error.message}`);
      console.error(error);
    }
  }

  async checkEnvironmentVariables() {
    logSection('Environment Variables Analysis');
    
    // Check for environment files
    for (const envFile of CONFIG.ENV_FILES) {
      if (fs.existsSync(envFile)) {
        logSuccess(`Found ${envFile}`);
        try {
          const content = fs.readFileSync(envFile, 'utf8');
          const lines = content.split('\n').filter(line => line.trim() && !line.startsWith('#'));
          
          for (const line of lines) {
            const [key, value] = line.split('=');
            if (key && value) {
              logInfo(`  ${key}=${value}`);
              
              // Check for suspicious values
              if (key.includes('VITE_BACKEND_URL') && value.includes('localhost')) {
                logWarning(`  ${key} contains localhost - this may cause issues in production`);
                this.issues.push(`Environment variable ${key} contains localhost in ${envFile}`);
              }
            }
          }
        } catch (error) {
          logError(`Error reading ${envFile}: ${error.message}`);
        }
      } else {
        logInfo(`${envFile} not found (this is normal)`);
      }
    }

    // Check process.env for Vite variables
    logInfo('\nVite Environment Variables (if running in Node.js context):');
    const viteVars = Object.keys(process.env).filter(key => key.startsWith('VITE_'));
    
    if (viteVars.length > 0) {
      viteVars.forEach(key => {
        logInfo(`  ${key}=${process.env[key]}`);
      });
    } else {
      logInfo('  No VITE_ variables found in process.env');
    }
  }

  async checkBuildOutput() {
    logSection('Build Output Analysis');
    
    if (!fs.existsSync(CONFIG.BUILD_DIR)) {
      logError(`Build directory ${CONFIG.BUILD_DIR} does not exist`);
      this.issues.push('Build directory missing - run "npm run build" first');
      return;
    }

    logSuccess(`Build directory exists: ${CONFIG.BUILD_DIR}`);
    
    // Check for main build files
    const expectedFiles = [
      'index.html',
      'assets'
    ];
    
    for (const file of expectedFiles) {
      const filePath = path.join(CONFIG.BUILD_DIR, file);
      if (fs.existsSync(filePath)) {
        logSuccess(`Found ${file}`);
      } else {
        logError(`Missing ${file}`);
        this.issues.push(`Missing build artifact: ${file}`);
      }
    }

    // Check index.html for environment variable injection
    const indexPath = path.join(CONFIG.BUILD_DIR, 'index.html');
    if (fs.existsSync(indexPath)) {
      const indexContent = fs.readFileSync(indexPath, 'utf8');
      
      // Look for script tags that might contain environment variables
      const scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
      let match;
      let foundEnvVars = false;
      
      while ((match = scriptRegex.exec(indexContent)) !== null) {
        const scriptContent = match[1];
        if (scriptContent.includes('VITE_BACKEND_URL') || scriptContent.includes('import.meta.env')) {
          foundEnvVars = true;
          logInfo('Found environment variable references in build');
          
          // Extract relevant lines
          const lines = scriptContent.split('\n');
          const envLines = lines.filter(line => 
            line.includes('VITE_BACKEND_URL') || line.includes('import.meta.env')
          );
          
          envLines.forEach(line => {
            logInfo(`  ${line.trim()}`);
          });
        }
      }
      
      if (!foundEnvVars) {
        logWarning('No environment variable references found in index.html');
        this.issues.push('Environment variables may not be properly injected into build');
      }
    }

    // Check assets directory for JS files
    const assetsPath = path.join(CONFIG.BUILD_DIR, 'assets');
    if (fs.existsSync(assetsPath)) {
      const assetFiles = fs.readdirSync(assetsPath);
      const jsFiles = assetFiles.filter(file => file.endsWith('.js'));
      
      logInfo(`Found ${jsFiles.length} JavaScript files in assets`);
      
      // Check the main JS file for API_BASE_URL
      const mainJsFile = jsFiles.find(file => file.includes('index')) || jsFiles[0];
      if (mainJsFile) {
        const jsPath = path.join(assetsPath, mainJsFile);
        const jsContent = fs.readFileSync(jsPath, 'utf8');
        
        // Look for API base URL configurations
        const apiUrlMatches = jsContent.match(/https:\/\/eqdatascraper.*?\.up\.railway\.app/g);
        if (apiUrlMatches) {
          logSuccess('Found Railway backend URLs in JavaScript:');
          apiUrlMatches.forEach(url => logInfo(`  ${url}`));
        } else {
          logWarning('No Railway backend URLs found in JavaScript');
          this.issues.push('Railway backend URLs not found in compiled JavaScript');
        }
        
        // Check for localhost references (bad in production)
        if (jsContent.includes('localhost')) {
          logWarning('Found localhost references in compiled JavaScript');
          this.issues.push('Localhost references found in production build');
        }
      }
    }
  }

  async checkNetworkConnectivity() {
    logSection('Network Connectivity Check');
    
    const endpoints = [
      { name: 'Production Frontend', url: CONFIG.FRONTEND_PROD },
      { name: 'Production Backend', url: CONFIG.BACKEND_PROD },
      { name: 'Backend Health', url: `${CONFIG.BACKEND_PROD}/api/health` }
    ];

    for (const endpoint of endpoints) {
      try {
        logInfo(`Testing ${endpoint.name}: ${endpoint.url}`);
        
        const startTime = Date.now();
        const response = await axios.get(endpoint.url, {
          timeout: 10000,
          headers: {
            'User-Agent': 'EQDataScraper-Debug/1.0'
          }
        });
        const endTime = Date.now();
        
        logSuccess(`${endpoint.name} responded in ${endTime - startTime}ms`);
        logInfo(`  Status: ${response.status}`);
        logInfo(`  Content-Type: ${response.headers['content-type']}`);
        
        if (response.headers['content-type']?.includes('application/json')) {
          const preview = JSON.stringify(response.data).substring(0, 100);
          logInfo(`  Data preview: ${preview}...`);
        }
        
      } catch (error) {
        logError(`${endpoint.name} failed: ${error.message}`);
        this.issues.push(`Network connectivity issue: ${endpoint.name} - ${error.message}`);
        
        if (error.response) {
          logInfo(`  Status: ${error.response.status}`);
          logInfo(`  Headers: ${JSON.stringify(error.response.headers)}`);
        }
      }
    }
  }

  async checkBackendAPI() {
    logSection('Backend API Endpoint Testing');
    
    for (const endpoint of CONFIG.TEST_ENDPOINTS) {
      const url = `${CONFIG.BACKEND_PROD}${endpoint}`;
      
      try {
        logInfo(`Testing ${endpoint}: ${url}`);
        
        const response = await axios.get(url, {
          timeout: 15000,
          headers: {
            'Accept': 'application/json',
            'User-Agent': 'EQDataScraper-Debug/1.0'
          }
        });
        
        logSuccess(`${endpoint} responded successfully`);
        logInfo(`  Status: ${response.status}`);
        
        // Special handling for specific endpoints
        if (endpoint === '/api/health') {
          logInfo(`  Health Data: ${JSON.stringify(response.data)}`);
        } else if (endpoint === '/api/classes') {
          logInfo(`  Classes Count: ${response.data.length || 'N/A'}`);
        } else if (endpoint === '/api/cache-status') {
          const cacheKeys = Object.keys(response.data);
          logInfo(`  Cache Keys: ${cacheKeys.length} (${cacheKeys.slice(0, 3).join(', ')}...)`);
        }
        
      } catch (error) {
        logError(`${endpoint} failed: ${error.message}`);
        this.issues.push(`Backend API issue: ${endpoint} - ${error.message}`);
        
        if (error.response) {
          logInfo(`  Response Status: ${error.response.status}`);
          logInfo(`  Response Body: ${JSON.stringify(error.response.data)}`);
        }
      }
    }
  }

  async checkFrontendBuild() {
    logSection('Frontend Build Configuration');
    
    // Check package.json
    if (fs.existsSync(CONFIG.PACKAGE_JSON)) {
      const packageJson = JSON.parse(fs.readFileSync(CONFIG.PACKAGE_JSON, 'utf8'));
      
      logInfo('Build Scripts:');
      Object.entries(packageJson.scripts || {}).forEach(([key, value]) => {
        if (key.includes('build') || key.includes('start') || key.includes('preview')) {
          logInfo(`  ${key}: ${value}`);
        }
      });
      
      logInfo('Dependencies:');
      const relevantDeps = ['vue', 'vite', 'axios', 'pinia'];
      relevantDeps.forEach(dep => {
        if (packageJson.dependencies?.[dep]) {
          logInfo(`  ${dep}: ${packageJson.dependencies[dep]}`);
        }
      });
    }

    // Check vite.config.js
    if (fs.existsSync(CONFIG.VITE_CONFIG)) {
      const viteConfig = fs.readFileSync(CONFIG.VITE_CONFIG, 'utf8');
      
      logInfo('Vite Configuration:');
      
      // Look for proxy configuration
      if (viteConfig.includes('proxy')) {
        logInfo('  Proxy configuration found');
        const proxyMatch = viteConfig.match(/proxy:\s*{([^}]+)}/);
        if (proxyMatch) {
          logInfo(`  Proxy config: ${proxyMatch[1].trim()}`);
        }
      }
      
      // Look for environment variable handling
      if (viteConfig.includes('env')) {
        logInfo('  Environment variable handling found');
      }
    }
  }

  async checkRailwayConfiguration() {
    logSection('Railway Configuration Analysis');
    
    // Note: This would require Railway CLI or API access
    // For now, we'll provide guidance on what to check
    
    logInfo('Railway Configuration Checklist:');
    logInfo('  □ VITE_BACKEND_URL environment variable set in frontend service');
    logInfo('  □ Backend service is deployed and running');
    logInfo('  □ Services are in the same Railway project');
    logInfo('  □ No localhost references in production environment variables');
    logInfo('  □ Build command includes environment variable injection');
    
    this.recommendations.push('Verify Railway environment variables in dashboard');
    this.recommendations.push('Check Railway service logs for startup errors');
    this.recommendations.push('Ensure Railway build process includes "npm run build"');
  }

  async performEndToEndTest() {
    logSection('End-to-End API Flow Test');
    
    try {
      // Test the full flow that the frontend would perform
      logInfo('Simulating frontend API calls...');
      
      // 1. Health check
      const healthResponse = await axios.get(`${CONFIG.BACKEND_PROD}/api/health`, {
        timeout: 10000
      });
      logSuccess('Health check passed');
      
      // 2. Cache status
      const cacheResponse = await axios.get(`${CONFIG.BACKEND_PROD}/api/cache-status`, {
        timeout: 10000
      });
      logSuccess('Cache status check passed');
      
      // 3. Spell system removed - skip spell tests
      logInfo('Spell system has been removed - skipping spell endpoint tests');
      
      // 4. Test search functionality removed - spell search disabled
      logInfo('Spell search functionality has been removed');
      try {
        // Test items endpoint instead
        const itemResponse = await axios.get(`${CONFIG.BACKEND_PROD}/api/items/search?q=sword`, {
          timeout: 10000
        });
        logSuccess(`Item search functionality works (${itemResponse.data.items?.length || 0} results)`);
      } catch (error) {
        logError(`Search functionality failed: ${error.message}`);
        this.issues.push(`Search API not working: ${error.message}`);
      }
      
    } catch (error) {
      logError(`End-to-end test failed: ${error.message}`);
      this.issues.push(`End-to-end test failure: ${error.message}`);
    }
  }

  printSummary() {
    logHeader('Debugging Summary');
    
    if (this.issues.length === 0) {
      logSuccess('No issues detected! The application should be working correctly.');
    } else {
      logError(`Found ${this.issues.length} issue(s):`);
      this.issues.forEach((issue, index) => {
        logError(`  ${index + 1}. ${issue}`);
      });
    }
    
    if (this.recommendations.length > 0) {
      logInfo('\nRecommendations:');
      this.recommendations.forEach((rec, index) => {
        logInfo(`  ${index + 1}. ${rec}`);
      });
    }
    
    logInfo('\nNext Steps:');
    logInfo('  1. Fix any environment variable issues');
    logInfo('  2. Rebuild and redeploy if build artifacts are incorrect');
    logInfo('  3. Check Railway service logs for runtime errors');
    logInfo('  4. Test API endpoints directly in browser');
    logInfo('  5. Verify CORS settings if cross-origin requests are failing');
    
    logSection('Debug Commands to Try');
    logInfo('Test backend health directly:');
    logInfo(`  curl ${CONFIG.BACKEND_PROD}/api/health`);
    logInfo('\nTest frontend build locally:');
    logInfo('  npm run build && npm run preview');
    logInfo('\nCheck Railway logs:');
    logInfo('  railway logs --service frontend');
    logInfo('  railway logs --service backend');
  }
}

// Run the debugger
if (require.main === module) {
  const debugTool = new ProductionDebugger();
  debugTool.runAllChecks().catch(console.error);
}

module.exports = ProductionDebugger;