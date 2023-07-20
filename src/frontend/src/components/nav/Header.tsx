import { Container, Group, Tabs } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useNavigate, useParams } from 'react-router-dom';

import { navTabs as mainNavTabs } from '../../defaults/links';
import { InvenTreeStyle } from '../../globalStyle';
import { ColorToggle } from '../items/ColorToggle';
import { ScanButton } from '../items/ScanButton';
import { MainMenu } from './MainMenu';
import { NavHoverMenu } from './NavHoverMenu';
import { NavigationDrawer } from './NavigationDrawer';

export function Header() {
  const { classes } = InvenTreeStyle();
  const [drawerOpened, { open: openDrawer, close }] = useDisclosure(false);

  return (
    <div className={classes.layoutHeader}>
      <NavigationDrawer opened={drawerOpened} close={close} />
      <Container className={classes.layoutHeaderSection} size={'xl'}>
        <Group position="apart">
          <Group>
            <NavHoverMenu openDrawer={openDrawer} />
            <NavTabs />
          </Group>
          <Group>
            <ScanButton />
            <ColorToggle />
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
