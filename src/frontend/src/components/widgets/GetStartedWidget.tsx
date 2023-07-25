import { Trans } from '@lingui/macro';
import { Title } from '@mantine/core';

import { CardsCarousel } from '../items/CardsCarousel';

export function GetStartedWidget() {
  return (
    <span>
      <Title order={5}>
        <Trans>Getting started</Trans>
      </Title>
      <CardsCarousel />
    </span>
  );
}
