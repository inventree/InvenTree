import {
  ActionIcon,
  Container,
  Group,
  Indicator,
  Tabs,
  Text,
  Tooltip
} from '@mantine/core';
import { useDisclosure, useDocumentVisibility } from '@mantine/hooks';
import { IconBell, IconSearch } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useEffect, useMemo, useState } from 'react';
import { useMatch, useNavigate } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { navigateToLink } from '@lib/functions/Navigation';
import { t } from '@lingui/core/macro';
import { useShallow } from 'zustand/react/shallow';
import { api } from '../../App';
import type { NavigationUIFeature } from '../../components/plugins/PluginUIFeatureTypes';
import { getNavTabs } from '../../defaults/links';
import { usePluginUIFeature } from '../../hooks/UsePluginUIFeature';
import * as classes from '../../main.css';
import { useServerApiState } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';
import { ScanButton } from '../buttons/ScanButton';
import { SpotlightButton } from '../buttons/SpotlightButton';
import { Alerts } from './Alerts';
import { MainMenu } from './MainMenu';
import { NavHoverMenu } from './NavHoverMenu';
import { NavigationDrawer } from './NavigationDrawer';
import { NotificationDrawer } from './NotificationDrawer';
import { SearchDrawer } from './SearchDrawer';

export function Header() {
  const [setNavigationOpen, navigationOpen] = useLocalState(
    useShallow((state) => [state.setNavigationOpen, state.navigationOpen])
  );
  const [server] = useServerApiState(useShallow((state) => [state.server]));
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

  const { isLoggedIn, isStaff } = useUserState();
  const [notificationCount, setNotificationCount] = useState<number>(0);
  const globalSettings = useGlobalSettingsState();

  const navbar_message = useMemo(() => {
    return server.customize?.navbar_message;
  }, [server.customize]);

  const visibility = useDocumentVisibility();

  // Fetch number of notifications for the current user
  const notifications = useQuery({
    queryKey: ['notification-count'],
    enabled: isLoggedIn() && visibility === 'visible',
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
    // Refetch every minute, *if* the tab is visible
    refetchInterval: 60 * 1000,
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
            {globalSettings.isSet('NOTIFICATIONS_ENABLE') && (
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
            )}
            <Alerts />
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

  const extraNavs = usePluginUIFeature<NavigationUIFeature>({
    featureType: 'navigation',
    context: {}
  });

  const tabs: ReactNode[] = useMemo(() => {
    const _tabs: ReactNode[] = [];

    const mainNavTabs = getNavTabs(user);

    // static content
    mainNavTabs.forEach((tab) => {
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
    // dynamic content
    extraNavs.forEach((nav) => {
      _tabs.push(
        <Tabs.Tab
          value={nav.options.title}
          key={nav.options.key}
          onClick={(event: any) =>
            navigateToLink(nav.options.options.url, navigate, event)
          }
        >
          {nav.options.title}
        </Tabs.Tab>
      );
    });

    return _tabs;
  }, [extraNavs, navTabs, user, withIcons]);

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
