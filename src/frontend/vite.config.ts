import react from '@vitejs/plugin-react';
import { platform, release } from 'node:os';
import { defineConfig, splitVendorChunkPlugin } from 'vite';

const IS_IN_WSL = platform().includes('WSL') || release().includes('WSL');

if (IS_IN_WSL) {
  console.log('WSL detected: using polling for file system events');
}

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
      },
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: true
      },
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: true
      }
    },
    watch: {
      // use polling only for WSL as the file system doesn't trigger notifications for Linux apps
      // ref: https://github.com/vitejs/vite/issues/1153#issuecomment-785467271
      usePolling: IS_IN_WSL
    }
  }
});
