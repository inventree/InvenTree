import { t } from '@lingui/macro';
import { Accordion } from '@mantine/core';

import { StylishText } from '../../components/items/StylishText';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useUserState } from '../../states/UserState';
import BuildAllocatedStockTable from '../../tables/build/BuildAllocatedStockTable';
import BuildLineTable from '../../tables/build/BuildLineTable';
import PartBuildAllocationsTable from '../../tables/part/PartBuildAllocationsTable';
import SalesOrderAllocationTable from '../../tables/sales/SalesOrderAllocationTable';

export default function PartAllocationPanel({ part }: { part: any }) {
  const user = useUserState();

  return (
    <>
      <Accordion
        multiple={true}
        defaultValue={['buildallocations', 'salesallocations']}
      >
        {part.component && user.hasViewRole(UserRoles.build) && (
          <Accordion.Item value="buildallocations" key="buildallocations">
            <Accordion.Control>
              <StylishText size="lg">{t`Build Order Allocations`}</StylishText>
            </Accordion.Control>
            <Accordion.Panel>
              <PartBuildAllocationsTable partId={part.pk} />
            </Accordion.Panel>
          </Accordion.Item>
        )}
        {part.salable && user.hasViewRole(UserRoles.sales_order) && (
          <Accordion.Item value="salesallocations" key="salesallocations">
            <Accordion.Control>
              <StylishText size="lg">{t`Sales Order Allocations`}</StylishText>
            </Accordion.Control>
            <Accordion.Panel>
              <SalesOrderAllocationTable
                partId={part.pk}
                modelField="order"
                modelTarget={ModelType.salesorder}
                showOrderInfo
              />
            </Accordion.Panel>
          </Accordion.Item>
        )}
      </Accordion>
    </>
  );
}
