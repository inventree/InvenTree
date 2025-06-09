// This config file is used to build the common InvenTree UI library components,
// which are distributed via NPM - to facilitate plugin development

import { resolve } from 'node:path';
import { defineConfig, mergeConfig } from 'vite';
import dts from 'vite-plugin-dts';
import viteConfig from './vite.config';

import { __INVENTREE_VERSION_INFO__ } from './version-info';

export default defineConfig((cfg) =>
  mergeConfig(
    viteConfig(cfg),
    defineConfig({
      resolve: {},
      build: {
        minify: false,
        manifest: true,
        outDir: 'dist',
        sourcemap: true,
        rollupOptions: {
          output: {
            preserveModules: true,
            preserveModulesRoot: 'lib'
          },
          external: ['react', 'react-dom']
        },
        lib: {
          entry: {
            index: resolve(__dirname, 'lib/index.ts')
          },
          name: 'InvenTree',
          formats: ['es']
        }
      },
      plugins: [
        dts({
          entryRoot: 'lib',
          outDir: 'dist',
          insertTypesEntry: true, // Ensures `dist/index.d.ts` is generated
          exclude: ['node_modules/**/*', 'src/**/*']
        })
      ],
      define: {
        ...__INVENTREE_VERSION_INFO__
      }
    })
  )
);
