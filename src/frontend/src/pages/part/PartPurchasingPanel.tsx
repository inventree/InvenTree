import { t } from '@lingui/macro';
import { Accordion, Skeleton } from '@mantine/core';

import { OrderHistoryChart } from '../../components/charts/OrderHistoryChart';
import { StylishText } from '../../components/items/StylishText';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import PartPurchaseOrdersTable from '../../tables/part/PartPurchaseOrdersTable';

/**
 * Construct a panel displaying purchase order information for a given part.
 */
export default function PartPurchasingPanel({ part }: { part: any }) {
  return (
    <Accordion multiple defaultValue={['purchase-orders']}>
      <Accordion.Item value="purchase-orders">
        <Accordion.Control>
          <StylishText size="lg">{t`Purchase Orders`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          {part.pk ? (
            <PartPurchaseOrdersTable partId={part.pk} />
          ) : (
            <Skeleton />
          )}
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value="purchase-history">
        <Accordion.Control>
          <StylishText size="lg">{t`Purchase History`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          {part.pk ? (
            <OrderHistoryChart
              endpoint={ApiEndpoints.purchase_order_history}
              params={{
                part: part.pk
              }}
            />
          ) : (
            <Skeleton />
          )}
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
