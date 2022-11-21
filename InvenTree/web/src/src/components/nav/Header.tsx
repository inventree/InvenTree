import { useState } from 'react';
import {
  Container,
  UnstyledButton,
  Group,
  Text,
  Menu,
  Tabs,
  Burger,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconLogout,
  IconHeart,
  IconSettings,
  IconChevronDown,
  IconDashboard,
  IconUserCircle,
} from '@tabler/icons';
import { ColorToggle } from '../items/ColorToggle';
import { InvenTreeLogo } from '../items/InvenTreeLogo';
import { useNavigate, useParams } from 'react-router-dom';
import { useStyles } from '../../globalStyle';
import { Link } from 'react-router-dom';
import { useLocalState } from "../../contex/LocalState";
import { useApiState } from "../../contex/ApiState";
import { tabs } from '../../defaults';


export function Header() {
  const { classes, theme, cx } = useStyles();
  const [opened, { toggle }] = useDisclosure(false);
  const [userMenuOpened, setUserMenuOpened] = useState(false);
  const navigate = useNavigate();
  const { tabValue } = useParams();
  const [hostKey, hostList] = useLocalState(state => [state.hostKey, state.hostList]);
  const [username, servername] = useApiState(state => [state.user.name, state.server.instance]);

  const items = tabs.map((tab) => (
    <Tabs.Tab value={tab.name} key={tab.name}>
      {tab.text}
    </Tabs.Tab>
  ));

  return (
    <div className={classes.header}>
      <Container className={classes.mainSection}>
        <Group position="apart">
          <Group><InvenTreeLogo />{hostList[hostKey].name}|{servername}</Group>
          <Burger opened={opened} onClick={toggle} className={classes.burger} size="sm" />
          <Group>
            <ColorToggle />
            <Menu
              width={260}
              position="bottom-end"
              transition="pop-top-right"
              onClose={() => setUserMenuOpened(false)}
              onOpen={() => setUserMenuOpened(true)}
            >
              <Menu.Target>
                <UnstyledButton
                  className={cx(classes.user, { [classes.userActive]: userMenuOpened })}
                >
                  <Group spacing={7}>
                    <Text weight={500} size="sm" sx={{ lineHeight: 1 }} mr={3}>{username}</Text>
                    <IconChevronDown size={12} stroke={1.5} />
                  </Group>
                </UnstyledButton>
              </Menu.Target>
              <Menu.Dropdown>
                <Menu.Item icon={<IconHeart size={14} color={theme.colors.red[6]} stroke={1.5} />}>
                  Notifications
                </Menu.Item>
                <Menu.Item icon={<IconUserCircle size={14} stroke={1.5} />} component={Link} to="/profile/user">
                  Profile
                </Menu.Item>

                <Menu.Label>Settings</Menu.Label>
                <Menu.Item icon={<IconSettings size={14} stroke={1.5} />}>Account settings</Menu.Item>
                <Menu.Item icon={<IconLogout size={14} stroke={1.5} />} component={Link} to="/logout">Logout</Menu.Item>
              </Menu.Dropdown>
            </Menu>
          </Group>
        </Group>
      </Container>
      <Container>
        <Tabs
          defaultValue="Home"
          variant="outline"
          classNames={{
            root: classes.tabs,
            tabsList: classes.tabsList,
            tab: classes.tab,
          }}
          value={tabValue}
          onTabChange={(value) => value == '/' ? navigate('/') : navigate(`/${value}`)}
        >
          <Tabs.List><Tabs.Tab value={'/'} key={'dash'} icon={<IconDashboard size={14} />} />{items}</Tabs.List>
        </Tabs>
      </Container>
    </div>
  );
}
