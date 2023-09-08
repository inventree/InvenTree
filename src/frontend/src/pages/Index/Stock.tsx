import { Trans } from '@lingui/macro';
import { Group } from '@mantine/core';

import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { StockItemTable } from '../../components/tables/stock/StockItemTable';

export default function Stock() {
  return (
    <>
      <Group>
        <StylishText>
          <Trans>Stock Items</Trans>
        </StylishText>
        <PlaceholderPill />
      </Group>
      <StockItemTable />
    </>
  );
}
