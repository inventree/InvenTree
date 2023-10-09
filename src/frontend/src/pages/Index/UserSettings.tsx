import { t } from '@lingui/macro';
import { LoadingOverlay, Stack, Text } from '@mantine/core';
import {
  IconBellCog,
  IconDeviceDesktop,
  IconDeviceDesktopAnalytics,
  IconFileAnalytics,
  IconSearch,
  IconUserCircle
} from '@tabler/icons-react';
import { useEffect, useMemo } from 'react';

import { PlaceholderPanel } from '../../components/items/Placeholder';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { SettingType } from '../../components/settings/SettingItem';
import { SettingList } from '../../components/settings/SettingList';
import { useInstance } from '../../hooks/UseInstance';

/**
 * User settings page
 */
export default function UserSettings() {
  // Query manager for user settings
  const {
    instance: settings,
    refreshInstance: reloadSettings,
    instanceQuery: settingsQuery
  } = useInstance({
    url: '/settings/user/',
    hasPrimaryKey: false,
    fetchOnMount: true,
    defaultValue: []
  });

  const userSettingsPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'account',
        label: t`Account`,
        icon: <IconUserCircle />
      },
      {
        name: 'dashboard',
        label: t`Dashboard`,
        icon: <IconDeviceDesktopAnalytics />
      },
      {
        name: 'display',
        label: t`Display Options`,
        icon: <IconDeviceDesktop />
      },
      {
        name: 'search',
        label: t`Search`,
        icon: <IconSearch />,
        content: (
          <SettingList settings={settings} keys={['SEARCH_PREVIEW_RESULTS']} />
        )
      },
      {
        name: 'notifications',
        label: t`Notifications`,
        icon: <IconBellCog />
      },
      {
        name: 'reporting',
        label: t`Reporting`,
        icon: <IconFileAnalytics />
      }
    ];
  }, [settings]);

  return (
    <>
      <Stack spacing="xs">
        <LoadingOverlay visible={settingsQuery.isFetching} />
        <PageDetail
          title={t`User Settings`}
          detail={<Text>TODO: Filler</Text>}
        />
        <PanelGroup panels={userSettingsPanels} />
      </Stack>
    </>
  );
}
