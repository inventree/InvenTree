// This config file is used to build the common InvenTree UI library components,
// which are distributed via NPM - to facilitate plugin development

import { resolve } from 'node:path';
import { defineConfig, mergeConfig } from 'vite';
import dts from 'vite-plugin-dts';
import viteConfig from './vite.config';

export default defineConfig((cfg) =>
  mergeConfig(
    viteConfig(cfg),
    defineConfig({
      resolve: {},
      build: {
        manifest: true,
        outDir: 'dist',
        sourcemap: true,
        rollupOptions: {
          output: {
            preserveModules: true,
            preserveModulesRoot: 'lib'
          },
          external: ['react', 'react-dom', '@mantine/core', '@mantine/hooks']
        },
        lib: {
          entry: {
            index: resolve(__dirname, 'lib/index.ts'),
            components: resolve(__dirname, 'lib/components/index.ts'),
            forms: resolve(__dirname, 'lib/forms/index.ts'),
            functions: resolve(__dirname, 'lib/functions/index.ts'),
            hooks: resolve(__dirname, 'lib/hooks/index.ts'),
            tables: resolve(__dirname, 'lib/tables/index.ts')
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
      ]
    })
  )
);
