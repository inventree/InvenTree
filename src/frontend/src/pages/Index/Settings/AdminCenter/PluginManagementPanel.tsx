import { Trans } from '@lingui/macro';
import { Alert, Stack, Title } from '@mantine/core';
import { IconAlertTriangle, IconInfoCircle } from '@tabler/icons-react';

import { GlobalSettingList } from '../../../../components/settings/SettingList';
import { PluginErrorTable } from '../../../../components/tables/plugin/PluginErrorTable';
import { PluginListTable } from '../../../../components/tables/plugin/PluginListTable';
import { useServerApiState } from '../../../../states/ApiState';

export default function PluginManagementPanel() {
  const pluginsEnabled = useServerApiState(
    (state) => state.server.plugins_enabled
  );

  return (
    <Stack>
      {!pluginsEnabled && (
        <Alert
          title={<Trans>Info</Trans>}
          icon={<IconInfoCircle />}
          color="blue"
        >
          <Trans>
            External plugins are not enabled for this InvenTree installation.
          </Trans>
        </Alert>
      )}

      <PluginListTable props={{}} />

      <Stack spacing={'xs'}>
        <Title order={5}>
          <Trans>Plugin Error Stack</Trans>
        </Title>
        <PluginErrorTable props={{}} />
      </Stack>

      <Stack spacing={'xs'}>
        <Title order={5}>
          <Trans>Plugin Settings</Trans>
        </Title>
        <GlobalSettingList
          keys={[
            'ENABLE_PLUGINS_SCHEDULE',
            'ENABLE_PLUGINS_EVENTS',
            'ENABLE_PLUGINS_URL',
            'ENABLE_PLUGINS_NAVIGATION',
            'ENABLE_PLUGINS_APP',
            'PLUGIN_ON_STARTUP'
          ]}
        />
      </Stack>
    </Stack>
  );
}
