import { Stack } from '@mantine/core';

import { PluginListTable } from '../../../../components/tables/plugin/PluginListTable';

export function PluginManagementPanel() {
  return (
    <Stack spacing="xs">
      <PluginListTable props={{}} />
    </Stack>
  );
}
