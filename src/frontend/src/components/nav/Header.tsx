import { Trans } from '@lingui/macro';
import {
  Container,
  Group,
  Menu,
  Tabs,
  Text,
  UnstyledButton
} from '@mantine/core';
import {
  IconChevronDown,
  IconHeart,
  IconLanguage,
  IconLogout,
  IconSettings,
  IconUserCircle
} from '@tabler/icons-react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { languages } from '../../contexts/LanguageContext';
import { navTabs } from '../../defaults/links';
import { doClassicLogout } from '../../functions/auth';
import { InvenTreeStyle } from '../../globalStyle';
import { useApiState } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';
import { ColorToggle } from '../items/ColorToggle';
import { PlaceholderPill } from '../items/Placeholder';
import { ScanButton } from '../items/ScanButton';
import { MegaHoverMenu } from './MegaHoverMenu';

export function Header() {
  const { classes } = InvenTreeStyle();
  const { tabValue } = useParams();
  const [locale] = useLocalState((state) => [state.language]);
  const [username] = useApiState((state) => [state.user?.name]);

  // Language
  function switchLanguage() {
    useLocalState.setState({
      language: languages[(languages.indexOf(locale) + 1) % languages.length]
    });
  }
  function enablePsuedo() {
    useLocalState.setState({ language: 'pseudo-LOCALE' });
  }

  return (
    <div className={classes.layoutHeader}>
      <Container className={classes.layoutHeaderSection} size={'xl'}>
        <Group position="apart">
          <Group>
            <MegaHoverMenu />
            <NavigationTabs tabValue={tabValue} />
          </Group>
          <Group>
            <ScanButton />
            <ColorToggle />
            <Menu width={260} position="bottom-end">
              <Menu.Target>
                <UnstyledButton className={classes.layoutHeaderUser}>
                  <Group spacing={7}>
                    <Text weight={500} size="sm" sx={{ lineHeight: 1 }} mr={3}>
                      {username}
                    </Text>
                    <IconChevronDown />
                  </Group>
                </UnstyledButton>
              </Menu.Target>
              <Menu.Dropdown>
                <Menu.Item icon={<IconHeart />}>
                  <Trans>Notifications</Trans>
                  <PlaceholderPill />
                </Menu.Item>
                <Menu.Item
                  icon={<IconUserCircle />}
                  component={Link}
                  to="/profile/user"
                >
                  <Trans>Profile</Trans>
                </Menu.Item>

                <Menu.Label>
                  <Trans>Settings</Trans>
                </Menu.Label>
                <Menu.Item icon={<IconLanguage />} onClick={switchLanguage}>
                  <Trans>Current language {locale}</Trans>
                </Menu.Item>
                <Menu.Item icon={<IconLanguage />} onClick={enablePsuedo}>
                  <Trans>Switch to pseudo language</Trans>
                </Menu.Item>
                <Menu.Item icon={<IconSettings />}>
                  <Trans>Account settings</Trans>
                  <PlaceholderPill />
                </Menu.Item>
                <Menu.Item
                  icon={<IconLogout />}
                  onClick={() => {
                    doClassicLogout();
                  }}
                >
                  <Trans>Logout</Trans>
                </Menu.Item>
              </Menu.Dropdown>
            </Menu>
          </Group>
        </Group>
      </Container>
    </div>
  );
}

function NavigationTabs({ tabValue }: { tabValue: string | undefined }) {
  const { classes } = InvenTreeStyle();
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
        {navTabs.map((tab) => (
          <Tabs.Tab value={tab.name} key={tab.name}>
            {tab.text}
          </Tabs.Tab>
        ))}
      </Tabs.List>
    </Tabs>
  );
}
