/*
 * This config file is used to build the common InvenTree UI library components,
 * which are distributed via NPM - to facilitate plugin development.
 *
 * Note that we externalize a number of common libraries,
 * so that plugins can use the same versions as the main InvenTree application.
 *
 * Externalizing libraries is critical here,
 * to ensure that the plugins do not bundle their own versions of these libraries,
 * so that the plugin uses the same React instance as the main application.
 */

import { resolve } from 'node:path';
import { defineConfig, mergeConfig } from 'vite';
import dts from 'vite-plugin-dts';
import { viteExternalsPlugin } from 'vite-plugin-externals';
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
            preserveModulesRoot: 'lib',
            globals: {
              react: 'React',
              'react-dom': 'ReactDOM',
              '@mantine/core': 'MantineCore',
              '@mantine/notifications': 'MantineNotifications'
            }
          },
          external: [
            'react',
            'react-dom',
            '@mantine/core',
            '@mantine/notifications'
          ]
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
        }),
        viteExternalsPlugin({
          react: 'React',
          'react-dom': 'ReactDOM',
          ReactDom: 'ReactDOM',
          '@mantine/core': 'MantineCore',
          '@mantine/notifications': 'MantineNotifications'
        })
      ],
      define: {
        ...__INVENTREE_VERSION_INFO__
      }
    })
  )
);
