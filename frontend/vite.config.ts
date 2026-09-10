import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/ — mirrors portfolio/web/vite.config.ts, no reason
// to diverge for Phase 0.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // avoids a CORS round-trip / hardcoded backend origin in api.ts during
      // dev; Phase 3 deploy config points this at the real backend service.
      '/api': 'http://127.0.0.1:8123',
    },
  },
})
