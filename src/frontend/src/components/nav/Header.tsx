import { Trans } from '@lingui/macro';
import {
  Anchor,
  Button,
  Container,
  Divider,
  Group,
  HoverCard,
  Menu,
  SimpleGrid,
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
import React, { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { useApiState } from '../../context/ApiState';
import { languages } from '../../context/LanguageContext';
import { useLocalState } from '../../context/LocalState';
import { tabs } from '../../defaults';
import { menuItems } from '../../defaults';
import { doClassicLogout } from '../../functions/auth';
import { InvenTreeStyle } from '../../globalStyle';
import { ColorToggle } from '../items/ColorToggle';
import { DocTooltip } from '../items/DocTooltip';
import { InvenTreeLogo } from '../items/InvenTreeLogo';
import { PlaceholderPill } from '../items/Placeholder';
import { ScanButton } from '../items/ScanButton';

export function Header() {
  const { classes } = InvenTreeStyle();
  const [userMenuOpened, setUserMenuOpened] = useState(false);
  const navigate = useNavigate();
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

  const navTabs = (
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
        {tabs.map((tab) => (
          <Tabs.Tab value={tab.name} key={tab.name}>
            {tab.text}
          </Tabs.Tab>
        ))}
      </Tabs.List>
    </Tabs>
  );
  return (
    <div className={classes.layoutHeader}>
      <Container className={classes.layoutHeaderSection} size={'xl'}>
        <Group position="apart">
          <Group>
            <MegaHoverMenu />
            {navTabs}
          </Group>
          <Group>
            <ScanButton />
            <ColorToggle />
            <Menu
              width={260}
              position="bottom-end"
              onClose={() => setUserMenuOpened(false)}
              onOpen={() => setUserMenuOpened(true)}
            >
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

function MegaHoverMenu() {
  const { classes, theme } = InvenTreeStyle();
  const [hostKey, hostList] = useLocalState((state) => [
    state.hostKey,
    state.hostList
  ]);
  const [servername] = useApiState((state) => [state.server.instance]);

  interface MenuLinkItem {
    title: string;
    description: string;
    detail?: string;
    link?: string;
    children?: React.ReactNode;
  }

  const MenuLinks = function name({ links }: { links: MenuLinkItem[] }) {
    let linksItems = links.map((item) => (
      <DocTooltip
        text={item.description}
        detail={item?.detail}
        link={item?.link}
        docchildren={item?.children}
      >
        <UnstyledButton className={classes.subLink} key={item.title}>
          <Text size="sm" fw={500}>
            {item.title}
          </Text>
        </UnstyledButton>
      </DocTooltip>
    ));
    return (
      <SimpleGrid cols={2} spacing={0}>
        {linksItems}
      </SimpleGrid>
    );
  };

  const data: MenuLinkItem[] = menuItems;

  return (
    <HoverCard width={600} position="bottom" shadow="md" withinPortal>
      <HoverCard.Target>
        <a href="#">
          <InvenTreeLogo />
        </a>
      </HoverCard.Target>

      <HoverCard.Dropdown sx={{ overflow: 'hidden' }}>
        <Group position="apart" px="md">
          <Anchor href="">
            <Text fw={500}>
              <Trans>Home</Trans>
            </Text>
          </Anchor>
          {hostList[hostKey].name}|{servername}
          <Anchor href="#" fz="xs">
            <Trans>View all</Trans>
          </Anchor>
        </Group>

        <Divider
          my="sm"
          mx="-md"
          color={theme.colorScheme === 'dark' ? 'dark.5' : 'gray.1'}
        />
        <MenuLinks links={data} />
        <div className={classes.headerDropdownFooter}>
          <Group position="apart">
            <div>
              <Text fw={500} fz="sm">
                <Trans>Get started</Trans>
              </Text>
              <Text size="xs" color="dimmed">
                <Trans>
                  Overview over high-level objects, functions and possible
                  usecases.
                </Trans>
              </Text>
            </div>
            <Button variant="default">
              <Trans>Get started</Trans>
            </Button>
          </Group>
        </div>
      </HoverCard.Dropdown>
    </HoverCard>
  );
}
