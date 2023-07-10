import { Trans } from '@lingui/macro';
import { Group } from '@mantine/core';

import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';

import { PartTable } from '../../components/tables/PartTables';

export default function Part() {
  return (
    <>
    <Group>
      <StylishText>
        <Trans>Parts</Trans>
      </StylishText>
      <PlaceholderPill />
    </Group>
    <PartTable />
    </>
  );
}
