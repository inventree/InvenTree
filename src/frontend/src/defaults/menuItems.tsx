import { Trans, t } from '@lingui/macro';
import { Image, Text } from '@mantine/core';

import { MenuLinkItem } from '../components/items/MenuLinks';

export const menuItems: MenuLinkItem[] = [
  {
    id: 'open-source',
    title: <Trans>Open source</Trans>,
    description: <Trans>This Pokémon’s cry is very loud and distracting</Trans>,
    detail: (
      <Trans>
        This Pokémon’s cry is very loud and distracting and more and more and
        more
      </Trans>
    ),
    link: 'https://www.google.com'
  }
];
