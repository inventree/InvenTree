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
      default_server?: string;
      show_server_selector: boolean;
    };
  }
}

// add settings for development
if (import.meta.env.DEV) {
  window.INVENTREE_SETTINGS = {
    server_list: {
      'mantine-cqj63coxn': {
        host: `${window.location.origin}/api/`,
        name: t`Current Server`
      },
      'mantine-u56l5jt85': {
        host: 'https://demo.inventree.org/api/',
        name: t`InvenTree Demo`
      }
    },
    default_server: 'mantine-cqj63coxn',
    show_server_selector: true
  };
}

window.INVENTREE_SETTINGS = {
  server_list: {},
  show_server_selector: false,

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
