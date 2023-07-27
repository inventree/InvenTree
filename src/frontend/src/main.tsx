import { t } from '@lingui/macro';
import React from 'react';
import ReactDOM from 'react-dom/client';

import App from './App';
import { HostList } from './states/states';

// define settings
declare global {
  interface Window {
    INVENTREE_SETTINGS: {
      server_list: HostList;
      default_server: string;
      show_server_selector: boolean;
    };
  }
}

const IS_DEV = import.meta.env.DEV;
const IS_NETLIFY = import.meta.env.VITE_NETLIFY === 'true';
const IS_SERVER_SELECTOR_DEV = IS_DEV || IS_NETLIFY;

window.INVENTREE_SETTINGS = {
  server_list: {
    'mantine-cqj63coxn': {
      host: `${window.location.origin}/api/`,
      name: t`Current Server`
    },
    ...(IS_SERVER_SELECTOR_DEV
      ? {
          'mantine-u56l5jt85': {
            host: 'https://demo.inventree.org/api/',
            name: t`InvenTree Demo`
          }
        }
      : {})
  },
  default_server: IS_NETLIFY ? 'mantine-u56l5jt85' : 'mantine-cqj63coxn', // use demo server for netlify previews
  show_server_selector: IS_SERVER_SELECTOR_DEV,

  // merge in settings that are already set via django's spa_view or for development
  ...((window.INVENTREE_SETTINGS || {}) as any)
};

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Redirect to /platform if on /
if (window.location.pathname === '/') {
  window.location.replace('/platform');
}
