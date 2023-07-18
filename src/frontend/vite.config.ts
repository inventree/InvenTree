import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: ['macros']
      }
    })
  ],
  build: {
    manifest: true,
    outDir: '../../InvenTree/web/static/web'
  }
});
