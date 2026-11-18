import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendTarget = env.VITE_API_BASE_URL || process.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  const host = env.VITE_HOST || process.env.VITE_HOST || '127.0.0.1'
  const port = parseInt(env.VITE_PORT || process.env.VITE_PORT || '5173', 10)

  return {
    plugins: [react()],
    base: './',
    server: {
      port,
      host,
      proxy: {
        '/api': {
          target: backendTarget,
          changeOrigin: true,
          secure: false,
        }
      }
    }
  }
})
