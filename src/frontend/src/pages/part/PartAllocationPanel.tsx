import { t } from '@lingui/core/macro';
import { Accordion } from '@mantine/core';

import { UserRoles } from '@lib/enums/Roles';
import { StylishText } from '../../components/items/StylishText';
import { useUserState } from '../../states/UserState';
import PartBuildAllocationsTable from '../../tables/part/PartBuildAllocationsTable';
import PartSalesAllocationsTable from '../../tables/part/PartSalesAllocationsTable';

export default function PartAllocationPanel({ part }: Readonly<{ part: any }>) {
  const user = useUserState();

  return (
    <Accordion
      multiple={true}
      defaultValue={['buildallocations', 'salesallocations']}
    >
      {part.component && user.hasViewRole(UserRoles.build) && (
        <Accordion.Item value='buildallocations' key='buildallocations'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Build Order Allocations`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <PartBuildAllocationsTable partId={part.pk} />
          </Accordion.Panel>
        </Accordion.Item>
      )}
      {part.salable && user.hasViewRole(UserRoles.sales_order) && (
        <Accordion.Item value='salesallocations' key='salesallocations'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Sales Order Allocations`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <PartSalesAllocationsTable partId={part.pk} />
          </Accordion.Panel>
        </Accordion.Item>
      )}
    </Accordion>
  );
}
