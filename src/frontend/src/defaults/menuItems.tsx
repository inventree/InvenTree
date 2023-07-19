import { Trans, t } from '@lingui/macro';
import { Image, Text } from '@mantine/core';

import { MenuLinkItem } from '../components/items/MenuLinks';

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
    link: '/profile/',
    doctext: <Trans>User attributes and design settings.</Trans>
  }
];
