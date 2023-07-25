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

window.INVENTREE_SETTINGS = {
  server_list: {},
  show_server_selector: true,

  // merge in settings that are already set via django's spa_view
  ...((window.INVENTREE_SETTINGS || {}) as any)
};

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
