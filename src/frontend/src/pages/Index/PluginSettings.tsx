import { t } from '@lingui/macro';
import { LoadingOverlay, Stack } from '@mantine/core';
import { IconPlugConnected } from '@tabler/icons-react';
import { useMemo } from 'react';

import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { PluginListTable } from '../../components/tables/plugin/PluginListTable';
import { useInstance } from '../../hooks/UseInstance';
import { ApiPaths } from '../../states/ApiState';

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
        <PageDetail title={t`Plugin Settings`} />
        <PanelGroup pageKey="plugin-settings" panels={pluginPanels} />
      </Stack>
    </>
  );
}
