import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default ({ mode }) => {
  // load .env files (Vite exposes them as plain strings)
  const env = loadEnv(mode, process.cwd(), '')
  // Priority: loaded env file -> process.env (docker-compose) -> fallback
  const proxyTarget = env.VITE_API_URL || process.env.VITE_API_URL || 'http://localhost:5000'

  return defineConfig({
    plugins: [react()],
    server: {
      host: true,
      proxy: {
        '/project-delay': {
          target: proxyTarget,
          changeOrigin: true,
          secure: false,
        },
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          secure: false,
        },
        '/phase9': {
          target: proxyTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  })
}
