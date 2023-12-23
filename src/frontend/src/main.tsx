import * as Sentry from '@sentry/react';
import React from 'react';
import ReactDOM from 'react-dom/client';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

import { HostList } from './states/states';
import MainView from './views/MainView';

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

// Filter out any settings that are not defined
let loaded_vals = (window.INVENTREE_SETTINGS || {}) as any;
Object.keys(loaded_vals).forEach((key) => {
  if (loaded_vals[key] === undefined) {
    delete loaded_vals[key];
    // check for empty server list
  } else if (key === 'server_list' && loaded_vals[key].length === 0) {
    delete loaded_vals[key];
  }
});

window.INVENTREE_SETTINGS = {
  server_list: {
    'mantine-cqj63coxn': {
      host: `${window.location.origin}/`,
      name: 'Current Server'
    },
    ...(IS_DEV_OR_DEMO
      ? {
          'mantine-u56l5jt85': {
            host: 'https://demo.inventree.org/',
            name: 'InvenTree Demo'
          }
        }
      : {})
  },
  default_server: IS_DEMO ? 'mantine-u56l5jt85' : 'mantine-cqj63coxn',
  show_server_selector: IS_DEV_OR_DEMO,

  // merge in settings that are already set via django's spa_view or for development
  ...loaded_vals
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
    <MainView />
  </React.StrictMode>
);

// Redirect to base url if on /
if (window.location.pathname === '/') {
  window.location.replace(`/${base_url}`);
}
