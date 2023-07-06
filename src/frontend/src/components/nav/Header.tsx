import { Trans } from '@lingui/macro';
import {
  Container,
  Group,
  Image,
  Menu,
  Tabs,
  Text,
  UnstyledButton
} from '@mantine/core';
import { Anchor, Button, Divider, HoverCard, SimpleGrid } from '@mantine/core';
import {
  IconChevronDown,
  IconDashboard,
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

  const items = tabs.map((tab) => (
    <Tabs.Tab value={tab.name} key={tab.name}>
      {tab.text}
    </Tabs.Tab>
  ));

  return (
    <div className={classes.layoutHeader}>
      <Container className={classes.layoutHeaderSection} size={'xl'}>
        <Group position="apart">
          <Group>
            <MegaHoverMenu />
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
      <Container size={'xl'}>
        <Tabs
          defaultValue="Home"
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
            <Tabs.Tab value={'/'} key={'dash'} icon={<IconDashboard />} />
            {items}
          </Tabs.List>
        </Tabs>
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

  const data: MenuLinkItem[] = [
    {
      title: 'Open source',
      description: 'This Pokémon’s cry is very loud and distracting',
      detail:
        'This Pokémon’s cry is very loud and distracting and more and more and more',
      link: 'https://www.google.com'
    },
    {
      title: 'Free for everyone',
      description: 'The fluid of Smeargle’s tail secretions changes',
      detail:
        'The fluid of Smeargle’s tail secretions changes in the intensity',
      link: 'https://www.google.com',
      children: (
        <>
          <Text>abc</Text>
          <Image
            mx="auto"
            src="https://images.unsplash.com/photo-1511216335778-7cb8f49fa7a3?ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&ixlib=rb-1.2.1&auto=format&fit=crop&w=720&q=80"
            alt="Random image"
          />
          <Text>
            Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam
            nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam
            erat, sed diam voluptua. At vero eos et accusam et justo duo dolores
            et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est
            Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur
            sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore
            et dolore magna aliquyam erat, sed diam voluptua. At vero eos et
            accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren,
            no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum
            dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod
            tempor invidunt ut labore et dolore magna aliquyam erat, sed diam
            voluptua. At vero eos et accusam et justo duo dolores et ea rebum.
            Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum
            dolor sit amet. Duis autem vel eum iriure dolor in hendrerit in
            vulputate velit esse molestie consequat, vel illum dolore eu feugiat
            nulla facilisis at vero eros et accumsan et iusto odio dignissim qui
            blandit praesent luptatum zzril delenit augue duis dolore the
            feugait nulla facilisi. Lorem ipsum dolor sit amet, consectetuer
            adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet
            dolore magna aliquam erat volutpat. Ut wisi enim ad minim veniam,
            quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut
            aliquip ex ea commodo consequat. Duis autem vel eum iriure dolor in
            hendrerit in vulputate velit esse molestie consequat, vel illum
            dolore eu feugiat nulla facilisis at vero eros et accumsan et iusto
            odio dignissim qui blandit praesent luptatum zzril delenit augue
            duis dolore the feugait nulla facilisi. Name liber tempor cum soluta
            nobis eleifend option congue nihil imperdiet doming id quod mazim
            placerat facer possim assume. Lorem ipsum dolor sit amet,
            consectetuer adipiscing elit, sed diam nonummy nibh euismod
            tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut wisi
            enim ad minim veniam, quis nostrud exerci tation ullamcorper
            suscipit lobortis nisl ut aliquip ex ea commodo consequat. Duis
            autem vel eum iriure dolor in hendrerit in vulputate velit esse
            molestie consequat, vel illum dolore eu feugiat nulla facilisis. At
            vero eos et accusam et justo duo dolores et ea rebum. Stet clita
            kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit
            amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed
            diam nonumy eirmod tempor invidunt ut labore et dolore magna
            aliquyam erat, sed diam voluptua. At vero eos et accusam et justo
            duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata
            sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet,
            consetetur sadipscing elitr, At accusam aliquyam diam diam dolore
            dolores duo eirmod eos erat, et nonumy sed tempor et et invidunt
            justo labore Stet clita ea et gubergren, kasd magna no rebum.
            sanctus sea sed takimata ut vero voluptua. est Lorem ipsum dolor sit
            amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed
            diam nonumy eirmod tempor invidunt ut labore et dolore magna
            aliquyam erat. Consetetur sadipscing elitr, sed diam nonumy eirmod
            tempor invidunt ut labore et dolore magna aliquyam erat, sed diam
            voluptua. At vero eos et accusam et justo duo dolores et ea rebum.
            Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum
            dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing
            elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore
            magna aliquyam erat, sed diam voluptua. At vero eos et accusam et
            justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea
            takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor
          </Text>
        </>
      )
    },
    {
      title: 'Documentation',
      description: 'Yanma is capable of seeing 360 degrees without'
    },
    {
      title: 'Security',
      description: 'The shell’s rounded shape and the grooves on its.'
    },
    {
      title: 'Analytics',
      description: 'This Pokémon uses its flying ability to quickly chase'
    },
    {
      title: 'Notifications',
      description: 'Combusken battles with the intensely hot flames it spews'
    }
  ];

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
