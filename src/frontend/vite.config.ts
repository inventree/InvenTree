import { platform, release } from 'node:os';
import { codecovVitePlugin } from '@codecov/vite-plugin';
import { vanillaExtractPlugin } from '@vanilla-extract/vite-plugin';
import react from '@vitejs/plugin-react';
import license from 'rollup-plugin-license';
import { defineConfig, splitVendorChunkPlugin } from 'vite';
import istanbul from 'vite-plugin-istanbul';

import { __INVENTREE_VERSION_INFO__ } from './version-info';

// Detect if the current environment is WSL
// Required for enabling file system polling
const IS_IN_WSL = platform().includes('WSL') || release().includes('WSL');

if (IS_IN_WSL) {
  console.log('WSL detected: using polling for file system events');
}

// Output directory for the built files
const OUTPUT_DIR = '../../src/backend/InvenTree/web/static/web';

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  return {
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
            file: `${OUTPUT_DIR}/.vite/dependencies.json`,
            template(dependencies) {
              return JSON.stringify(dependencies);
            }
          }
        }
      }),
      istanbul({
        include: ['src/*', 'lib/*'],
        exclude: ['node_modules', 'test/'],
        extension: ['.js', '.ts', '.tsx'],
        requireEnv: true
      }),
      codecovVitePlugin({
        enableBundleAnalysis: process.env.CODECOV_TOKEN !== undefined,
        bundleName: 'pui_v1',
        uploadToken: process.env.CODECOV_TOKEN
      })
    ],
    // When building, set the base path to an empty string
    // This is required to ensure that the static path prefix is observed
    base: command == 'build' ? '' : undefined,
    build: {
      manifest: true,
      outDir: OUTPUT_DIR,
      sourcemap: true
    },
    resolve: {
      alias: {
        '@lib': '/lib'
      }
    },
    server: {
      proxy: {
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
        // Use polling only for WSL as the file system doesn't trigger notifications for Linux apps
        // Ref: https://github.com/vitejs/vite/issues/1153#issuecomment-785467271
        usePolling: IS_IN_WSL
      }
    },
    define: {
      ...__INVENTREE_VERSION_INFO__
    }
  };
});
