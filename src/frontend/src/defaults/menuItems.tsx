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
    text: <Trans>Profile page</Trans>,
    link: '/profile/user',
    doctext: <Trans>User attributes and design settings.</Trans>
  },
  {
    id: 'scan',
    text: <Trans>Scanning</Trans>,
    link: '/scan',
    doctext: <Trans>View for interactive scanning and multiple actions.</Trans>,
    highlight: true
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
