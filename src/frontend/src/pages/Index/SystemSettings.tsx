import { t } from '@lingui/macro';
import { LoadingOverlay, Stack } from '@mantine/core';
import { useEffect, useMemo } from 'react';

import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { useInstance } from '../../hooks/UseInstance';

/**
 * System settings page
 */
export default function SystemSettings() {
  // Query manager for global system settings
  const {
    instance: settings,
    refreshInstance: reloadSettings,
    instanceQuery: settingsQuery
  } = useInstance('/settings/global/', null, {});

  // Load settings on page load
  useEffect(() => {
    settingsQuery.refetch();
  }, []);

  const systemSettingsPanels: PanelType[] = useMemo(() => {
    return [];
  }, [settings]);

  return (
    <>
      <Stack spacing="xs">
        <LoadingOverlay visible={settingsQuery.isFetching} />
        <PageDetail title={t`System Settings`} />
        <PanelGroup panels={systemSettingsPanels} />
      </Stack>
    </>
  );
}
