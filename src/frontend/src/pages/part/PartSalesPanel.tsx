import { t } from '@lingui/macro';
import { Accordion, Skeleton } from '@mantine/core';

import { OrderHistoryChart } from '../../components/charts/OrderHistoryChart';
import { StylishText } from '../../components/items/StylishText';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { SalesOrderTable } from '../../tables/sales/SalesOrderTable';

/**
 * Construct a panel displaying sales order information for a given part.
 */
export default function PartSalesPanel({ part }: { part: any }) {
  return (
    <Accordion multiple defaultValue={['sales-orders']}>
      <Accordion.Item value="sales-orders">
        <Accordion.Control>
          <StylishText size="lg">{t`Sales Orders`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          {part.pk ? <SalesOrderTable partId={part.pk} /> : <Skeleton />}
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value="sales-history">
        <Accordion.Control>
          <StylishText size="lg">{t`Sales History`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          {part.pk ? (
            <OrderHistoryChart
              endpoint={ApiEndpoints.sales_order_history}
              params={{
                part: part.pk,
                include_variants: true
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
