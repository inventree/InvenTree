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
  } = useInstance('/settings/user/', null, {});

  // Load settings on page load
  useEffect(() => {
    console.log('Fetching settings:');
    settingsQuery.refetch();
  }, []);

  const userSettings: SettingType[] = useMemo(() => {
    console.log('loaded settings:', settings);

    if (settings) {
      return settings as SettingType[];
    } else {
      return [];
    }
  }, [settings]);

  const userSettingsPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'account',
        label: t`Account`,
        icon: <IconUserCircle size="18" />,
        content: <PlaceholderPanel />
      },
      {
        name: 'dashboard',
        label: t`Dashboard`,
        icon: <IconDeviceDesktopAnalytics size="18" />,
        content: <PlaceholderPanel />
      },
      {
        name: 'display',
        label: t`Display Options`,
        icon: <IconDeviceDesktop size="18" />,
        content: <PlaceholderPanel />
      },
      {
        name: 'search',
        label: t`Search`,
        icon: <IconSearch size="18" />,
        content: <PlaceholderPanel />
      },
      {
        name: 'notifications',
        label: t`Notifications`,
        icon: <IconBellCog size="18" />,
        content: <PlaceholderPanel />
      },
      {
        name: 'reporting',
        label: t`Reporting`,
        icon: <IconFileAnalytics size="18" />,
        content: <PlaceholderPanel />
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
