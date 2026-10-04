import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  ActionIcon,
  Avatar,
  Box,
  Divider,
  Group,
  Indicator,
  Menu,
  Skeleton,
  Text,
  Tooltip,
  UnstyledButton,
  useMantineColorScheme
} from '@mantine/core';
import { useDisclosure, useDocumentVisibility } from '@mantine/hooks';
import {
  IconBell,
  IconChevronDown,
  IconExclamationCircle,
  IconHelpCircle,
  IconInfoCircle,
  IconLogout,
  IconMoonStars,
  IconQrcode,
  IconSearch,
  IconSettings,
  IconSun,
  IconUserBolt,
  IconUserCog
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useShallow } from 'zustand/react/shallow';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { useInvenTreeHotkeys } from '@lib/functions/Events';
import { api } from '../../App';
import { aboutInvenTree } from '../../defaults/links';
import { doLogout } from '../../functions/auth';
import { useServerApiState } from '../../states/ServerApiState';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import { ScanButton } from '../buttons/ScanButton';
import { SpotlightButton } from '../buttons/SpotlightButton';
import { Alerts } from './Alerts';
import { NotificationDrawer } from './NotificationDrawer';
import { SearchDrawer } from './SearchDrawer';


export function TopBar() {
  const navigate = useNavigate();
  const [notificationCount, setNotificationCount] = useState<number>(0);
  const { isLoggedIn, user } = useUserState();
  const [username] = useUserState(useShallow((s) => [s.username]));
  const globalSettings = useGlobalSettingsState();
  const userSettings = useUserSettingsState();
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  const isDark = colorScheme === 'dark';

  const [
    searchDrawerOpened,
    { open: openSearchDrawer, close: closeSearchDrawer }
  ] = useDisclosure(false);

  const [
    notificationDrawerOpened,
    { open: openNotificationDrawer, close: closeNotificationDrawer }
  ] = useDisclosure(false);

  useInvenTreeHotkeys([
    ['/', t`Open search`, () => openSearchDrawer()],
    ['mod+/', t`Open search`, () => openSearchDrawer()]
  ]);

  const visibility = useDocumentVisibility();

  const notifications = useQuery({
    queryKey: ['notification-count-topbar', visibility],
    enabled: isLoggedIn() && visibility === 'visible',
    queryFn: async () => {
      if (!isLoggedIn()) return null;
      return api
        .get(apiUrl(ApiEndpoints.notifications_list), {
          params: { read: false, limit: 1 }
        })
        .then((response: any) => {
          setNotificationCount(response?.data?.count ?? 0);
          return response.data ?? null;
        });
    },
    refetchInterval: 60 * 1000,
    refetchOnMount: true,
    refetchOnWindowFocus: false,
    staleTime: 30 * 1000
  });

  const iconStyle = {
    width: 34,
    height: 34,
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)',
    border: isDark ? '1px solid rgba(255,255,255,0.09)' : '1px solid rgba(0,0,0,0.08)',
    transition: 'background 0.15s ease',
    cursor: 'pointer'
  } as const;

  const userInitial = username ? username().charAt(0).toUpperCase() : '?';

  return (
    <>
      <SearchDrawer opened={searchDrawerOpened} onClose={closeSearchDrawer} />
      <NotificationDrawer
        opened={notificationDrawerOpened}
        onClose={() => {
          notifications.refetch();
          closeNotificationDrawer();
        }}
      />

      <Box
        style={{
          height: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 20px',
          borderBottom: isDark
            ? '1px solid rgba(255,255,255,0.08)'
            : '1.5px solid #e2e8f0',
          background: isDark ? '#0f172a' : '#ffffff',
          boxShadow: isDark
            ? '0 1px 3px rgba(0,0,0,0.3)'
            : '0 1px 4px rgba(15,23,42,0.03)',
          flexShrink: 0
        }}
      >
        {/* Left: Page title area (breadcrumb or empty) */}
        <Box />

        {/* Right: Utility icons + user */}
        <Group gap={6} wrap='nowrap'>
          {/* Search */}
          <Tooltip label={t`Search`} position='bottom'>
            <ActionIcon
              variant='subtle'
              size='lg'
              radius='md'
              onClick={openSearchDrawer}
              aria-label='open-search'
            >
              <IconSearch size={18} />
            </ActionIcon>
          </Tooltip>

          {/* Spotlight */}
          {userSettings.isSet('SHOW_SPOTLIGHT') && (
            <SpotlightButton hotkey />
          )}

          {/* Barcode */}
          {globalSettings.isSet('BARCODE_ENABLE') && <ScanButton hotkey />}

          {/* Notifications */}
          <Indicator
            radius='lg'
            size='16'
            label={notificationCount}
            color='red'
            disabled={notificationCount <= 0}
            inline
          >
            <Tooltip label={t`Notifications`} position='bottom'>
              <ActionIcon
                variant='subtle'
                size='lg'
                radius='md'
                onClick={openNotificationDrawer}
                aria-label='open-notifications'
              >
                <IconBell size={18} />
              </ActionIcon>
            </Tooltip>
          </Indicator>

          {/* Alerts */}
          <Alerts />

          <Divider orientation='vertical' mx={4} />

          {/* User Menu */}
          <Menu width={220} position='bottom-end' shadow='lg'>
            <Menu.Target>
              <UnstyledButton
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '4px 8px',
                  borderRadius: 8,
                  transition: 'background 0.15s ease'
                }}
                className='topbar-user-btn'
              >
                <Avatar
                  size={32}
                  radius='xl'
                  style={{
                    fontWeight: 700,
                    background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
                    color: '#ffffff',
                    boxShadow: '0 2px 8px rgba(2, 132, 199, 0.35)'
                  }}
                >
                  {userInitial}
                </Avatar>
                <Box style={{ textAlign: 'left' }}>
                  {username() ? (
                    <Text size='sm' fw={600} lh={1.2}>
                      {username()}
                    </Text>
                  ) : (
                    <Skeleton height={14} width={60} />
                  )}
                  <Text size='xs' c='dimmed' lh={1.2}>
                    {user?.is_superuser
                      ? t`Super Admin`
                      : user?.is_staff
                        ? t`Admin`
                        : t`User`}
                  </Text>
                </Box>
                <IconChevronDown size={14} style={{ opacity: 0.5 }} />
              </UnstyledButton>
            </Menu.Target>

            <Menu.Dropdown>
              <Menu.Label>
                <Trans>Account</Trans>
              </Menu.Label>

              <Menu.Item
                leftSection={<IconUserCog size={14} />}
                component={Link}
                to='/settings/user'
              >
                <Trans>User Settings</Trans>
              </Menu.Item>

              {user?.is_staff && (
                <Menu.Item
                  leftSection={<IconSettings size={14} />}
                  component={Link}
                  to='/settings/system'
                >
                  <Trans>System Settings</Trans>
                </Menu.Item>
              )}

              {user?.is_staff && (
                <Menu.Item
                  leftSection={<IconUserBolt size={14} />}
                  component={Link}
                  to='/settings/admin'
                >
                  <Trans>Admin Center</Trans>
                </Menu.Item>
              )}

              <Menu.Divider />


              <Menu.Item
                onClick={() => aboutInvenTree()}
                leftSection={<IconHelpCircle size={14} />}
              >
                <Trans>About InvenTree</Trans>
              </Menu.Item>

              <Menu.Divider />

              <Menu.Item
                leftSection={<IconLogout size={14} />}
                color='red'
                onClick={() => doLogout(navigate)}
              >
                <Trans>Logout</Trans>
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      </Box>

      <style>{`
        .topbar-user-btn:hover {
          background: rgba(0,0,0,0.05) !important;
        }
      `}</style>
    </>
  );
}
