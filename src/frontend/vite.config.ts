import react from '@vitejs/plugin-react';
import { platform } from 'node:os';
import { defineConfig, splitVendorChunkPlugin } from 'vite';

const isInWsl = () => platform().includes('WSL');

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: ['macros']
      }
    }),
    splitVendorChunkPlugin()
  ],
  build: {
    manifest: true,
    outDir: '../../InvenTree/web/static/web'
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: true
      }
    },
    watch: {
      usePolling: isInWsl()
    }
  }
});
