import { t } from '@lingui/macro';
import { LoadingOverlay, Stack } from '@mantine/core';
import { IconPlugConnected } from '@tabler/icons-react';
import { useMemo } from 'react';

import { PanelGroup, PanelType } from '../../../components/nav/PanelGroup';
import { SettingsHeader } from '../../../components/nav/SettingsHeader';
import { PluginListTable } from '../../../components/tables/plugin/PluginListTable';
import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useInstance } from '../../../hooks/UseInstance';

/**
 * Plugins settings page
 */
export default function PluginSettings() {
  // Query manager for global plugin settings
  const {
    instance: settings,
    refreshInstance: reloadSettings,
    instanceQuery: settingsQuery
  } = useInstance({
    endpoint: ApiPaths.settings_global_list,
    hasPrimaryKey: false,
    refetchOnMount: true,
    defaultValue: []
  });

  const pluginPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'plugins',
        label: t`Plugins`,
        icon: <IconPlugConnected />,
        content: (
          <Stack spacing="xs">
            <PluginListTable props={{}} />
          </Stack>
        )
      }
    ];
  }, []);

  return (
    <>
      <Stack spacing="xs">
        <LoadingOverlay visible={settingsQuery.isFetching} />
        <SettingsHeader title={t`Plugin Settings`} switch_condition={false} />
        <PanelGroup pageKey="plugin-settings" panels={pluginPanels} />
      </Stack>
    </>
  );
}
