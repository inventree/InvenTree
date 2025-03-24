import {
  ActionIcon,
  Alert,
  Container,
  Group,
  Indicator,
  Menu,
  Tabs,
  Text,
  Tooltip
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconBell,
  IconExclamationCircle,
  IconSearch
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useEffect, useMemo, useState } from 'react';
import { useMatch, useNavigate } from 'react-router-dom';

import { t } from '@lingui/macro';
import { api } from '../../App';
import { getNavTabs } from '../../defaults/links';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { navigateToLink } from '../../functions/navigation';
import * as classes from '../../main.css';
import { apiUrl, useServerApiState } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';
import { ScanButton } from '../buttons/ScanButton';
import { SpotlightButton } from '../buttons/SpotlightButton';
import { MainMenu } from './MainMenu';
import { NavHoverMenu } from './NavHoverMenu';
import { NavigationDrawer } from './NavigationDrawer';
import { NotificationDrawer } from './NotificationDrawer';
import { SearchDrawer } from './SearchDrawer';

interface AlertInfo {
  key: string;
  title: string;
  message: string;
}

export function Header() {
  const user = useUserState();

  const [setNavigationOpen, navigationOpen] = useLocalState((state) => [
    state.setNavigationOpen,
    state.navigationOpen
  ]);
  const [server] = useServerApiState((state) => [state.server]);
  const [navDrawerOpened, { open: openNavDrawer, close: closeNavDrawer }] =
    useDisclosure(navigationOpen);
  const [
    searchDrawerOpened,
    { open: openSearchDrawer, close: closeSearchDrawer }
  ] = useDisclosure(false);

  const [
    notificationDrawerOpened,
    { open: openNotificationDrawer, close: closeNotificationDrawer }
  ] = useDisclosure(false);

  const { isLoggedIn } = useUserState();
  const [notificationCount, setNotificationCount] = useState<number>(0);
  const globalSettings = useGlobalSettingsState();

  const navbar_message = useMemo(() => {
    return server.customize?.navbar_message;
  }, [server.customize]);

  const [dismissed, setDismissed] = useState<string[]>([]);

  const alerts: AlertInfo[] = useMemo(() => {
    const _alerts: AlertInfo[] = [];

    if (server?.debug_mode) {
      _alerts.push({
        key: 'debug',
        title: t`Debug Mode`,
        message: t`The server is running in debug mode.`
      });
    }

    if (server?.worker_running == false) {
      _alerts.push({
        key: 'worker',
        title: t`Background Worker`,
        message: t`The background worker process is not running.`
      });
    }

    if (globalSettings.isSet('SERVER_RESTART_REQUIRED')) {
      _alerts.push({
        key: 'restart',
        title: t`Server Restart`,
        message: t`The server requires a restart to apply changes.`
      });
    }

    const n_migrations =
      Number.parseInt(globalSettings.getSetting('_PENDING_MIGRATIONS')) ?? 0;

    if (n_migrations > 0) {
      _alerts.push({
        key: 'migrations',
        title: t`Database Migrations`,
        message: t`There are pending database migrations.`
      });
    }

    return _alerts.filter((alert) => !dismissed.includes(alert.key));
  }, [server, dismissed, globalSettings]);

  // Fetch number of notifications for the current user
  const notifications = useQuery({
    queryKey: ['notification-count'],
    enabled: isLoggedIn(),
    queryFn: async () => {
      if (!isLoggedIn()) {
        return null;
      }

      try {
        const params = {
          params: {
            read: false,
            limit: 1
          }
        };
        const response = await api
          .get(apiUrl(ApiEndpoints.notifications_list), params)
          .catch(() => {
            return null;
          });
        setNotificationCount(response?.data?.count ?? 0);
        return response?.data ?? null;
      } catch (error) {
        return null;
      }
    },
    refetchInterval: 30000,
    refetchOnMount: true
  });

  // Sync Navigation Drawer state with zustand
  useEffect(() => {
    if (navigationOpen === navDrawerOpened) return;
    setNavigationOpen(navDrawerOpened);
  }, [navDrawerOpened]);

  useEffect(() => {
    if (navigationOpen === navDrawerOpened) return;
    if (navigationOpen) openNavDrawer();
    else closeNavDrawer();
  }, [navigationOpen]);

  return (
    <div className={classes.layoutHeader}>
      <SearchDrawer opened={searchDrawerOpened} onClose={closeSearchDrawer} />
      <NavigationDrawer opened={navDrawerOpened} close={closeNavDrawer} />
      <NotificationDrawer
        opened={notificationDrawerOpened}
        onClose={() => {
          notifications.refetch();
          closeNotificationDrawer();
        }}
      />
      <Container className={classes.layoutHeaderSection} size='100%'>
        <Group justify='space-between'>
          <Group>
            <NavHoverMenu openDrawer={openNavDrawer} />
            <NavTabs />
          </Group>
          {navbar_message && (
            <Text>
              {/* biome-ignore lint/security/noDangerouslySetInnerHtml: <explanation> */}
              <span dangerouslySetInnerHTML={{ __html: navbar_message }} />
            </Text>
          )}
          <Group>
            <Tooltip position='bottom-end' label={t`Search`}>
              <ActionIcon
                onClick={openSearchDrawer}
                variant='transparent'
                aria-label='open-search'
              >
                <IconSearch />
              </ActionIcon>
            </Tooltip>
            <SpotlightButton />
            {globalSettings.isSet('BARCODE_ENABLE') && <ScanButton />}
            <Indicator
              radius='lg'
              size='18'
              label={notificationCount}
              color='red'
              disabled={notificationCount <= 0}
              inline
            >
              <Tooltip position='bottom-end' label={t`Notifications`}>
                <ActionIcon
                  onClick={openNotificationDrawer}
                  variant='transparent'
                  aria-label='open-notifications'
                >
                  <IconBell />
                </ActionIcon>
              </Tooltip>
            </Indicator>
            {user.isStaff() && alerts.length > 0 && (
              <Menu withinPortal={true} position='bottom-end'>
                <Menu.Target>
                  <Tooltip position='bottom-end' label={t`Alerts`}>
                    <ActionIcon
                      variant='transparent'
                      aria-label='open-alerts'
                      color='red'
                    >
                      <IconExclamationCircle />
                    </ActionIcon>
                  </Tooltip>
                </Menu.Target>
                <Menu.Dropdown>
                  {alerts.map((alert) => (
                    <Menu.Item key={`alert-item-${alert.key}`}>
                      <Alert
                        withCloseButton
                        color='red'
                        title={alert.title}
                        onClose={() => setDismissed([...dismissed, alert.key])}
                      >
                        {alert.message}
                      </Alert>
                    </Menu.Item>
                  ))}
                </Menu.Dropdown>
              </Menu>
            )}
            <MainMenu />
          </Group>
        </Group>
      </Container>
    </div>
  );
}

function NavTabs() {
  const user = useUserState();
  const navigate = useNavigate();
  const match = useMatch(':tabName/*');
  const tabValue = match?.params.tabName;
  const navTabs = getNavTabs(user);
  const userSettings = useUserSettingsState();

  const withIcons: boolean = useMemo(
    () => userSettings.isSet('ICONS_IN_NAVBAR', false),
    [userSettings]
  );

  const tabs: ReactNode[] = useMemo(() => {
    const _tabs: ReactNode[] = [];

    navTabs.forEach((tab) => {
      if (tab.role && !user.hasViewRole(tab.role)) {
        return;
      }

      _tabs.push(
        <Tabs.Tab
          value={tab.name}
          key={tab.name}
          leftSection={
            withIcons &&
            tab.icon && (
              <ActionIcon variant='transparent'>{tab.icon}</ActionIcon>
            )
          }
          onClick={(event: any) =>
            navigateToLink(`/${tab.name}`, navigate, event)
          }
        >
          {tab.title}
        </Tabs.Tab>
      );
    });

    return _tabs;
  }, [navTabs, user, withIcons]);

  return (
    <Tabs
      defaultValue='home'
      classNames={{
        root: classes.tabs,
        list: classes.tabsList,
        tab: classes.tab
      }}
      value={tabValue}
    >
      <Tabs.List>{tabs.map((tab) => tab)}</Tabs.List>
    </Tabs>
  );
}
