import '@mantine/carousel/styles.css';
import '@mantine/charts/styles.css';
import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import '@mantine/notifications/styles.css';
import '@mantine/spotlight/styles.css';
import * as Sentry from '@sentry/react';
import 'mantine-contextmenu/styles.css';
import 'mantine-datatable/styles.css';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import * as MantineCore from '@mantine/core';
import * as MantineNotifications from '@mantine/notifications';
import * as React from 'react';
import * as ReactDOM from 'react-dom';
import * as ReactDOMClient from 'react-dom/client';
import './styles/overrides.css';

// Lingui imports (required for plugin translation)
import * as LinguiCore from '@lingui/core';
import * as LinguiReact from '@lingui/react';

import { getBaseUrl } from '@lib/functions/Navigation';
import type { HostList } from '@lib/types/Server';
import MainView from './views/MainView';

// define settings
declare global {
  interface Window {
    INVENTREE_SETTINGS: {
      server_list: HostList;
      default_server: string;
      show_server_selector: boolean;
      base_url?: string;
      api_host?: string;
      sentry_dsn?: string;
      environment?: string;
      mobile_mode?: 'default' | 'allow-ignore' | 'allow-always';
    };
    react: typeof React;
    React: typeof React;
    ReactDOM: typeof ReactDOM;
    ReactDOMClient: typeof ReactDOMClient;
    MantineCore: typeof MantineCore;
    MantineNotifications: typeof MantineNotifications;
  }
}

// Running in dev mode (i.e. vite)
export const IS_DEV = import.meta.env.DEV;
export const IS_DEMO = import.meta.env.VITE_DEMO === 'true';
export const IS_DEV_OR_DEMO = IS_DEV || IS_DEMO;

// Filter out any settings that are not defined
const loaded_vals = (window.INVENTREE_SETTINGS || {}) as any;

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
    ...(IS_DEV
      ? {
          'server-localhost': {
            host: 'http://localhost:8000',
            name: 'Localhost'
          }
        }
      : {}),
    ...(IS_DEV_OR_DEMO
      ? {
          'server-demo': {
            host: 'https://demo.inventree.org/',
            name: 'InvenTree Demo'
          }
        }
      : {}),
    'server-current': {
      host: `${window.location.origin}/`,
      name: 'Current Server'
    }
  },
  default_server: IS_DEV
    ? 'server-localhost'
    : IS_DEMO
      ? 'server-demo'
      : 'server-current',
  show_server_selector: IS_DEV_OR_DEMO,

  // Merge in settings that are already set via django's spa_view or for development
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

// Expose global objects for the plugin system
(window as any).React = React;
(window as any).ReactDOM = ReactDOM;
(window as any).ReactDOMClient = ReactDOMClient;
(window as any).MantineCore = MantineCore;
(window as any).MantineNotifications = MantineNotifications;
(window as any).LinguiCore = LinguiCore;
(window as any).LinguiReact = LinguiReact;

// Redirect to base url if on /
if (window.location.pathname === '/') {
  window.location.replace(`/${getBaseUrl()}`);
}

ReactDOMClient.createRoot(
  document.getElementById('root') as HTMLElement
).render(
  <React.StrictMode>
    <MainView />
  </React.StrictMode>
);
