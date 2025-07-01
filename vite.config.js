import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { readFileSync } from 'fs'
import { resolve } from 'path'

// Load configuration to get backend port
let backendPort = 5001
let frontendPort = 3000

// Try to load config.json if it exists
try {
  const configPath = resolve(process.cwd(), 'config.json')
  const configData = readFileSync(configPath, 'utf8')
  const config = JSON.parse(configData)
  backendPort = config.backend_port || 5001
  frontendPort = config.frontend_port || 3000
} catch (error) {
  // In production environments like Railway, config.json might not exist
  // This is expected and we'll use environment variables instead
}

// Override with environment variables (Railway provides PORT)
backendPort = parseInt(process.env.BACKEND_PORT) || backendPort
frontendPort = parseInt(process.env.PORT) || parseInt(process.env.FRONTEND_PORT) || frontendPort

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0', // Bind to all interfaces for Windows/WSL access
    port: frontendPort,
    proxy: {
      '/api': {
        target: `http://localhost:${backendPort}`,
        changeOrigin: true
      }
    }
  },
  preview: {
    host: '0.0.0.0',
    port: frontendPort,
    allowedHosts: 'all',
    strictPort: false
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
}) 