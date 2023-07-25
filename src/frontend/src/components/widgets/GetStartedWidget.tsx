import { Trans } from '@lingui/macro';
import { Title } from '@mantine/core';

import { GettingStartedCarousel } from '../items/GettingStartedCarousel';

export default function GetStartedWidget() {
  return (
    <span>
      <Title order={5}>
        <Trans>Getting started</Trans>
      </Title>
      <GettingStartedCarousel />
    </span>
  );
}
