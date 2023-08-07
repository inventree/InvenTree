import { Trans } from '@lingui/macro';
import { Group } from '@mantine/core';

import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { PurchaseOrderTable } from '../../components/tables/order/PurchaseOrderTable';

export default function Order() {
  return (
    <>
      <Group>
        <StylishText>
          <Trans>Orders</Trans>
        </StylishText>
        <PlaceholderPill />
      </Group>
      <PurchaseOrderTable />
    </>
  );
}
