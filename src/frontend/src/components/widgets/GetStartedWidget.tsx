import { t } from '@lingui/macro';
import { Divider } from '@mantine/core';

import { navDocLinks } from '../../defaults/links';
import { GettingStartedCarousel } from '../items/GettingStartedCarousel';
import { StylishText } from '../items/StylishText';

export default function GetStartedWidget() {
  return (
    <span>
      <StylishText size="xl">{t`Getting Started`}</StylishText>
      <GettingStartedCarousel items={navDocLinks} />
    </span>
  );
}
