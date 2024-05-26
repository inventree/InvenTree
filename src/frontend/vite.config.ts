import { vanillaExtractPlugin } from '@vanilla-extract/vite-plugin';
import react from '@vitejs/plugin-react';
import { platform, release } from 'node:os';
import license from 'rollup-plugin-license';
import { defineConfig, splitVendorChunkPlugin } from 'vite';
import istanbul from 'vite-plugin-istanbul';

const IS_IN_WSL = platform().includes('WSL') || release().includes('WSL');
const is_coverage = process.env.VITE_COVERAGE === 'true';

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
    vanillaExtractPlugin(),
    splitVendorChunkPlugin(),
    license({
      sourcemap: true,
      thirdParty: {
        includePrivate: true,
        multipleVersions: true,
        output: {
          file: '../backend/InvenTree/web/static/web/.vite/dependencies.json',
          template(dependencies) {
            return JSON.stringify(dependencies);
          }
        }
      }
    }),
    istanbul({
      include: 'src/*',
      exclude: ['node_modules', 'test/'],
      extension: ['.js', '.ts', '.tsx'],
      requireEnv: true
    })
  ],
  build: {
    manifest: true,
    outDir: '../../src/backend/InvenTree/web/static/web',
    sourcemap: is_coverage
  },
  server: {
    watch: {
      // use polling only for WSL as the file system doesn't trigger notifications for Linux apps
      // ref: https://github.com/vitejs/vite/issues/1153#issuecomment-785467271
      usePolling: IS_IN_WSL
    }
  }
});
