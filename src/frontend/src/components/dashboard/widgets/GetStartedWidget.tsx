import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import { useMemo } from 'react';

import { DocumentationLinks } from '../../../defaults/links';
import { GettingStartedCarousel } from '../../items/GettingStartedCarousel';
import { MenuLinkItem } from '../../items/MenuLinks';
import { StylishText } from '../../items/StylishText';

export default function GetStartedWidget() {
  const docLinks: MenuLinkItem[] = useMemo(() => DocumentationLinks(), []);

  return (
    <Stack>
      <StylishText size="xl">{t`Getting Started`}</StylishText>
      <GettingStartedCarousel items={docLinks} />
    </Stack>
  );
}
