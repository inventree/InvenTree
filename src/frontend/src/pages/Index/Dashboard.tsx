import { Trans } from '@lingui/macro';
import { Chip, Group, SimpleGrid, Text } from '@mantine/core';

import { DashboardItemProxy } from '../../components/DashboardItemProxy';
import { StylishText } from '../../components/items/StylishText';
import { dashboardItems } from '../../defaults/dashboardItems';
import { useLocalState } from '../../states/LocalState';

export default function Dashboard() {
  const [autoupdate, toggleAutoupdate] = useLocalState((state) => [
    state.autoupdate,
    state.toggleAutoupdate
  ]);

  return (
    <>
      <Group>
        <StylishText>
          <Trans>Dashboard</Trans>
        </StylishText>
        <Chip checked={autoupdate} onChange={() => toggleAutoupdate()}>
          <Trans>Autoupdate</Trans>
        </Chip>
      </Group>
      <Text>
        <Trans>
          This page is a replacement for the old start page with the same
          information. This page will be deprecated and replaced by the home
          page.
        </Trans>
      </Text>
      <SimpleGrid cols={4} pt="md">
        {dashboardItems.map((item) => (
          <DashboardItemProxy key={item.id} {...item} autoupdate={autoupdate} />
        ))}
      </SimpleGrid>
    </>
  );
}
