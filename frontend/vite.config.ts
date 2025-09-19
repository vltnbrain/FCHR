import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/ideas': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/healthz': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/users': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/emails': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/reviews': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/assignments': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
