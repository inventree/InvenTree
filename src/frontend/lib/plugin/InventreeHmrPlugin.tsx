import type { Plugin } from 'vite';

/**
 * Vite plugin which enables hot module replacement (HMR) for InvenTree plugin development.
 *
 * This is for use with the InvenTree plugin creator tool,
 * allowing frontend plugin code to be "live reloaded" during development.
 */
export default function InventreeHmrPlugin(): Plugin {
  const fileRegex = /\.(js|jsx|ts|tsx)(\?|$)/;

  const hmrBlock = [
    '',
    '// __inventree_hmr_injected__',
    'if (import.meta.hot) {',
    '  import.meta.hot.accept((newModule) => {',
    '    const key = new URL(import.meta.url).origin + new URL(import.meta.url).pathname;',
    '    window.__plugin_hmr_callbacks?.[key]?.forEach(callback => {',
    '      callback(newModule);',
    '    });',
    '  })',
    '}'
  ];

  return {
    name: 'inventree-hmr-plugin',
    enforce: 'post',

    transform(code, id) {
      if (!fileRegex.test(id)) return;
      if (id.includes('node_modules')) return;
      if (code.includes('__inventree_hmr_injected__')) return;

      return {
        code: code + hmrBlock.join('\n'),
        map: null
      };
    }
  };
}
