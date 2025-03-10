import {
  ActionIcon,
  Container,
  Group,
  Indicator,
  Tabs,
  Text
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconBell, IconSearch } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useEffect, useMemo, useState } from 'react';
import { useMatch, useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { navTabs as mainNavTabs } from '../../defaults/links';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { navigateToLink } from '../../functions/navigation';
import * as classes from '../../main.css';
import { apiUrl, useServerApiState } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';
import { ScanButton } from '../buttons/ScanButton';
import { SpotlightButton } from '../buttons/SpotlightButton';
import { MainMenu } from './MainMenu';
import { NavHoverMenu } from './NavHoverMenu';
import { NavigationDrawer } from './NavigationDrawer';
import { NotificationDrawer } from './NotificationDrawer';
import { SearchDrawer } from './SearchDrawer';

export function Header() {
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
            <ActionIcon
              onClick={openSearchDrawer}
              variant='transparent'
              aria-label='open-search'
            >
              <IconSearch />
            </ActionIcon>
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
              <ActionIcon
                onClick={openNotificationDrawer}
                variant='transparent'
                aria-label='open-notifications'
              >
                <IconBell />
              </ActionIcon>
            </Indicator>
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

  const tabs: ReactNode[] = useMemo(() => {
    const _tabs: ReactNode[] = [];

    mainNavTabs.forEach((tab) => {
      if (tab.role && !user.hasViewRole(tab.role)) {
        return;
      }

      _tabs.push(
        <Tabs.Tab
          value={tab.name}
          key={tab.name}
          onClick={(event: any) =>
            navigateToLink(`/${tab.name}`, navigate, event)
          }
        >
          {tab.text}
        </Tabs.Tab>
      );
    });

    return _tabs;
  }, [mainNavTabs, user]);

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
