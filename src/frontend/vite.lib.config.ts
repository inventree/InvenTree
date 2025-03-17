// This config file is used to build the common InvenTree UI library components,
// which are distributed via NPM - to facilitate plugin development

import { resolve } from 'node:path';
import { defineConfig, mergeConfig } from 'vite';

import mainConfig from './vite.config';

export default mergeConfig(
  mainConfig,
  defineConfig({
    build: {
      manifest: true,
      outDir: 'dist',
      sourcemap: true,
      rollupOptions: {
        external: ['React']
      },
      lib: {
        entry: {
          components: resolve(__dirname, 'lib/components.ts'),
          core: resolve(__dirname, 'lib/core.ts'),
          functions: resolve(__dirname, 'lib/functions.ts'),
          hooks: resolve(__dirname, 'lib/hooks.ts'),
          tables: resolve(__dirname, 'lib/tables.ts')
        },
        name: 'InvenTree',
        formats: ['es']
      }
    }
  })
);
