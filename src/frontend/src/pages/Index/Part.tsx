import { Trans } from '@lingui/macro';
import { Group } from '@mantine/core';

import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { PartListTable } from '../../components/tables/part/PartTable';

export default function Part() {
  return (
    <>
      <Group>
        <StylishText>
          <Trans>Parts</Trans>
        </StylishText>
        <PlaceholderPill />
      </Group>
      <PartListTable />
    </>
  );
}
