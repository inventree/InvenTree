// This config file is used to build the common InvenTree UI library components,
// which are distributed via NPM - to facilitate plugin development

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { defineConfig, mergeConfig } from 'vite';
import dts from 'vite-plugin-dts';
import viteConfig from './vite.config';

const packageJson = JSON.parse(readFileSync('./package.json', 'utf-8'));

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
        __INVENTREE_LIB_VERSION__: JSON.stringify(packageJson.version)
      }
    })
  )
);
