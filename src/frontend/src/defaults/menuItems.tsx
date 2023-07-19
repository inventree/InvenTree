import { Trans, t } from '@lingui/macro';
import { Image, Text } from '@mantine/core';

import { MenuLinkItem } from '../components/items/MenuLinks';

export const menuItems: MenuLinkItem[] = [
  {
    id: 'home',
    title: <Trans>Home</Trans>,
    highlight: true
  },
  {
    id: 'profile',
    title: <Trans>Profile page</Trans>,
    description: <Trans>User attributes and design settings.</Trans>
  }
];
