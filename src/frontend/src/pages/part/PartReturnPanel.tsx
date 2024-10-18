import { t } from '@lingui/macro';
import { Accordion, Skeleton } from '@mantine/core';

import { OrderHistoryChart } from '../../components/charts/OrderHistoryChart';
import { StylishText } from '../../components/items/StylishText';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ReturnOrderTable } from '../../tables/sales/ReturnOrderTable';

/**
 * Construct a panel displaying return order information for a given part.
 */
export default function PartReturnPanel({ part }: { part: any }) {
  return (
    <Accordion multiple defaultValue={['return-orders']}>
      <Accordion.Item value="return-orders">
        <Accordion.Control>
          <StylishText size="lg">{t`Return Orders`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          {part.pk ? <ReturnOrderTable partId={part.pk} /> : <Skeleton />}
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value="purchase-history">
        <Accordion.Control>
          <StylishText size="lg">{t`Return History`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          {part.pk ? (
            <OrderHistoryChart
              endpoint={ApiEndpoints.return_order_history}
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
