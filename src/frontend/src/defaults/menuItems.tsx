import { Trans } from '@lingui/macro';

import { MenuLinkItem } from '../components/items/MenuLinks';
import { IS_DEV_OR_DEMO } from '../main';

export const menuItems: MenuLinkItem[] = [
  {
    id: 'home',
    text: <Trans>Home</Trans>,
    link: '/',
    highlight: true
  },
  {
    id: 'profile',
    text: <Trans>Account settings</Trans>,
    link: '/settings/user',
    doctext: <Trans>User attributes and design settings.</Trans>
  },
  {
    id: 'scan',
    text: <Trans>Scanning</Trans>,
    link: '/scan',
    doctext: <Trans>View for interactive scanning and multiple actions.</Trans>,
    highlight: true
  },
  {
    id: 'dashboard',
    text: <Trans>Dashboard</Trans>,
    link: '/dashboard'
  },
  {
    id: 'parts',
    text: <Trans>Parts</Trans>,
    link: '/part/'
  },
  {
    id: 'stock',
    text: <Trans>Stock</Trans>,
    link: '/stock'
  },
  {
    id: 'build',
    text: <Trans>Build</Trans>,
    link: '/build/'
  },
  {
    id: 'purchasing',
    text: <Trans>Purchasing</Trans>,
    link: '/purchasing/'
  },
  {
    id: 'sales',
    text: <Trans>Sales</Trans>,
    link: '/sales/'
  },
  {
    id: 'settings-system',
    text: <Trans>System Settings</Trans>,
    link: '/settings/system'
  },
  {
    id: 'settings-admin',
    text: <Trans>Admin Center</Trans>,
    link: '/settings/admin'
  }
];

if (IS_DEV_OR_DEMO) {
  menuItems.push({
    id: 'playground',
    text: <Trans>Playground</Trans>,
    link: '/playground',
    highlight: true
  });
}
