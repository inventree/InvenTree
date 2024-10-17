import { t } from '@lingui/macro';
import { Accordion, Skeleton } from '@mantine/core';

import { StylishText } from '../../components/items/StylishText';
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
      <Accordion.Item value="sales-order-history">
        <Accordion.Control>
          <StylishText size="lg">{t`Sales Order History`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          {part.pk ? <div>hello world</div> : <Skeleton />}
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
