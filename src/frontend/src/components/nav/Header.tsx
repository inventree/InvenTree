import { ActionIcon, Container, Group, Indicator, Tabs } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconBell, IconSearch } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { api } from '../../App';
import { navTabs as mainNavTabs } from '../../defaults/links';
import { InvenTreeStyle } from '../../globalStyle';
import { ScanButton } from '../items/ScanButton';
import { MainMenu } from './MainMenu';
import { NavHoverMenu } from './NavHoverMenu';
import { NavigationDrawer } from './NavigationDrawer';
import { SearchDrawer } from './SearchDrawer';

export function Header() {
  const { classes } = InvenTreeStyle();
  const [navDrawerOpened, { open: openNavDrawer, close: closeNavDrawer }] =
    useDisclosure(false);
  const [
    searchDrawerOpened,
    { open: openSearchDrawer, close: closeSearchDrawer }
  ] = useDisclosure(false);

  const [notificationCount, setNotificationCount] = useState(0);

  // Fetch number of notifications for the current user
  const notifications = useQuery({
    queryKey: ['notifications'],
    queryFn: async () => {
      return api
        .get('/notifications/', {
          params: {
            read: false,
            limit: 1
          }
        })
        .then((response) => {
          setNotificationCount(response.data.count);
          return response.data;
        })
        .catch((error) => {
          console.error('Error fetching notifications:', error);
          return error;
        });
    },
    refetchOnMount: true,
    refetchOnWindowFocus: false
  });

  return (
    <div className={classes.layoutHeader}>
      <SearchDrawer opened={searchDrawerOpened} onClose={closeSearchDrawer} />
      <NavigationDrawer opened={navDrawerOpened} close={closeNavDrawer} />
      <Container className={classes.layoutHeaderSection} size={'xl'}>
        <Group position="apart">
          <Group>
            <NavHoverMenu openDrawer={openNavDrawer} />
            <NavTabs />
          </Group>
          <Group>
            <ScanButton />
            <ActionIcon onClick={openSearchDrawer}>
              <IconSearch />
            </ActionIcon>
            <ActionIcon>
              <Indicator
                radius="lg"
                size="lg"
                label={notificationCount}
                color="red"
                hidden={notificationCount == 0}
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
  const { classes } = InvenTreeStyle();
  const { tabValue } = useParams();
  const navigate = useNavigate();

  return (
    <Tabs
      defaultValue="home"
      classNames={{
        root: classes.tabs,
        tabsList: classes.tabsList,
        tab: classes.tab
      }}
      value={tabValue}
      onTabChange={(value) =>
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
