import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'happy-dom',
    globals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'dist/',
        'backend/',
        '**/*.config.js',
        'tests/setup.js'
      ]
    },
    setupFiles: ['./tests/setup.js']
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  define: {
    // Mock environment variables for testing
    'import.meta.env.VITE_BACKEND_URL': JSON.stringify('http://localhost:5999'),
    'import.meta.env.PROD': false
  }
})