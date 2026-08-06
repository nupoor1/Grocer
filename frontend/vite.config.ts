import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // dev only -- the production build (single Render service) needs no proxy since
      // the frontend and API share an origin there. api.ts always calls /api/* relative.
      "/api": "http://127.0.0.1:8000",
    },
  },
})
