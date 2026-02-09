import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { copyFileSync } from 'fs'

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'copy-extension-files',
      closeBundle() {
        // Copy extension files to dist after build
        copyFileSync('background.js', 'dist/background.js')
        copyFileSync('content.js', 'dist/content.js')
        copyFileSync('manifest.json', 'dist/manifest.json')
        console.log('✓ Copied extension files to dist/')
      }
    }
  ],
  base: './',  // Use relative paths for Chrome extension
  build: {
    rollupOptions: {
      input: {
        popup: 'index.html'
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name].[ext]'
      }
    }
  }
})