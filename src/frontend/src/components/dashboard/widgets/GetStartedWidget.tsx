import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { DocumentationLinks } from '../../../defaults/links';
import { GettingStartedCarousel } from '../../items/GettingStartedCarousel';
import { MenuLinkItem } from '../../items/MenuLinks';
import { StylishText } from '../../items/StylishText';

export default function GetStartedWidget() {
  const docLinks: MenuLinkItem[] = useMemo(() => DocumentationLinks(), []);

  return (
    <span>
      <StylishText size="xl">{t`Getting Started`}</StylishText>
      <GettingStartedCarousel items={docLinks} />
    </span>
  );
}
