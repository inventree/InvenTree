import { ActionIcon, Container, Group, Indicator, Tabs } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconBell, IconSearch } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { useMatch, useNavigate, useParams } from 'react-router-dom';

import { api } from '../../App';
import { navTabs as mainNavTabs } from '../../defaults/links';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import * as classes from '../../main.css';
import { apiUrl } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';
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

  const [notificationCount, setNotificationCount] = useState<number>(0);

  // Fetch number of notifications for the current user
  const notifications = useQuery({
    queryKey: ['notification-count'],
    queryFn: async () => {
      try {
        const params = {
          params: {
            read: false,
            limit: 1
          }
        };
        let response = await api.get(
          apiUrl(ApiEndpoints.notifications_list),
          params
        );
        setNotificationCount(response.data.count);
        return response.data;
      } catch (error) {
        return error;
      }
    },
    refetchInterval: 30000,
    refetchOnMount: true,
    refetchOnWindowFocus: false
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
      <Container className={classes.layoutHeaderSection} size="100%">
        <Group justify="apart">
          <Group>
            <NavHoverMenu openDrawer={openNavDrawer} />
            <NavTabs />
          </Group>
          <Group>
            <ActionIcon onClick={openSearchDrawer}>
              <IconSearch />
            </ActionIcon>
            <SpotlightButton />
            <ScanButton />
            <ActionIcon onClick={openNotificationDrawer}>
              <Indicator
                radius="lg"
                size="18"
                label={notificationCount}
                color="red"
                disabled={notificationCount <= 0}
              >
                <IconBell />
              </Indicator>
            </ActionIcon>
            <MainMenu />
          </Group>
        </Group>
      </Container>
    </div>
  );
}

function NavTabs() {
  const navigate = useNavigate();
  const match = useMatch(':tabName/*');
  const tabValue = match?.params.tabName;

  return (
    <Tabs
      defaultValue="home"
      classNames={{
        root: classes.tabs,
        list: classes.tabsList,
        tab: classes.tab
      }}
      value={tabValue}
      onChange={(value) =>
        value == '/' ? navigate('/') : navigate(`/${value}`)
      }
    >
      <Tabs.List>
        {mainNavTabs.map((tab) => (
          <Tabs.Tab value={tab.name} key={tab.name}>
            {tab.text}
          </Tabs.Tab>
        ))}
      </Tabs.List>
    </Tabs>
  );
}
