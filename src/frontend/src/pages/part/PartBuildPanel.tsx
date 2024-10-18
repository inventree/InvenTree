import { t } from '@lingui/macro';
import { Accordion, Skeleton } from '@mantine/core';

import { OrderHistoryChart } from '../../components/charts/OrderHistoryChart';
import { StylishText } from '../../components/items/StylishText';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { BuildOrderTable } from '../../tables/build/BuildOrderTable';

/**
 * Construct a panel displaying build order information for a given part.
 */
export default function PartBuildPanel({ part }: { part: any }) {
  return (
    <Accordion multiple defaultValue={['build-orders']}>
      <Accordion.Item value="build-orders">
        <Accordion.Control>
          <StylishText size="lg">{t`Build Orders`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          {part.pk ? <BuildOrderTable partId={part.pk} /> : <Skeleton />}
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value="build-history">
        <Accordion.Control>
          <StylishText size="lg">{t`Build History`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          {part.pk ? (
            <OrderHistoryChart
              endpoint={ApiEndpoints.build_order_history}
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
