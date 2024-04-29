import { Trans } from '@lingui/macro';

import { menuItemsCollection } from '../components/items/MenuLinks';
import { IS_DEV_OR_DEMO } from '../main';

export const menuItems: menuItemsCollection = {
  home: {
    id: 'home',
    text: <Trans>Home</Trans>,
    link: '/',
    highlight: true
  },
  profile: {
    id: 'profile',
    text: <Trans>Account settings</Trans>,
    link: '/settings/user',
    doctext: <Trans>User attributes and design settings.</Trans>
  },
  scan: {
    id: 'scan',
    text: <Trans>Scanning</Trans>,
    link: '/scan',
    doctext: <Trans>View for interactive scanning and multiple actions.</Trans>,
    highlight: true
  },
  dashboard: {
    id: 'dashboard',
    text: <Trans>Dashboard</Trans>,
    link: '/dashboard'
  },
  parts: {
    id: 'parts',
    text: <Trans>Parts</Trans>,
    link: '/part/'
  },
  stock: {
    id: 'stock',
    text: <Trans>Stock</Trans>,
    link: '/stock'
  },
  build: {
    id: 'build',
    text: <Trans>Build</Trans>,
    link: '/build/'
  },
  purchasing: {
    id: 'purchasing',
    text: <Trans>Purchasing</Trans>,
    link: '/purchasing/'
  },
  sales: {
    id: 'sales',
    text: <Trans>Sales</Trans>,
    link: '/sales/'
  },
  'settings-system': {
    id: 'settings-system',
    text: <Trans>System Settings</Trans>,
    link: '/settings/system'
  },
  'settings-admin': {
    id: 'settings-admin',
    text: <Trans>Admin Center</Trans>,
    link: '/settings/admin'
  }
};

if (IS_DEV_OR_DEMO) {
  menuItems['playground'] = {
    id: 'playground',
    text: <Trans>Playground</Trans>,
    link: '/playground',
    highlight: true
  };
}
