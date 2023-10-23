import * as Sentry from '@sentry/react';
import React from 'react';
import ReactDOM from 'react-dom/client';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

import App from './App';
import { HostList } from './states/states';

// define settings
declare global {
  interface Window {
    INVENTREE_SETTINGS: {
      server_list: HostList;
      default_server: string;
      show_server_selector: boolean;
      base_url: string;
      sentry_dsn?: string;
      environment?: string;
    };
  }
}

export const IS_DEV = import.meta.env.DEV;
export const IS_DEMO = import.meta.env.VITE_DEMO === 'true';
export const IS_DEV_OR_DEMO = IS_DEV || IS_DEMO;

window.INVENTREE_SETTINGS = {
  server_list: {
    localhost: {
      host: `${window.location.origin}/`,
      name: 'Current Server'
    },
    ...(IS_DEV_OR_DEMO
      ? {
          demo: {
            host: 'https://demo.inventree.org/',
            name: 'InvenTree Demo'
          }
        }
      : {})
  },
  default_server: IS_DEMO ? 'demo' : 'localhost',
  show_server_selector: IS_DEV_OR_DEMO,

  // merge in settings that are already set via django's spa_view or for development
  ...((window.INVENTREE_SETTINGS || {}) as any)
};

if (window.INVENTREE_SETTINGS.sentry_dsn) {
  console.log('Sentry enabled');
  Sentry.init({
    dsn: window.INVENTREE_SETTINGS.sentry_dsn,
    tracesSampleRate: 1.0,
    environment: window.INVENTREE_SETTINGS.environment || 'default'
  });
}

export const base_url = window.INVENTREE_SETTINGS.base_url || 'platform';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Redirect to base url if on /
if (window.location.pathname === '/') {
  window.location.replace(`/${base_url}`);
}
