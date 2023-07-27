import { Trans } from '@lingui/macro';
import { Group } from '@mantine/core';

import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { BuildOrderTable } from '../../components/tables/build/BuildOrderTable';

export default function Build() {
  return (
    <>
      <Group>
        <StylishText>
          <Trans>Build Orders</Trans>
        </StylishText>
        <PlaceholderPill />
      </Group>
      <BuildOrderTable />
    </>
  );
}
