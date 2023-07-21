import { Trans } from '@lingui/macro';
import { Group, Menu, Skeleton, Text, UnstyledButton } from '@mantine/core';
import {
  IconChevronDown,
  IconHeart,
  IconLanguage,
  IconLogout,
  IconSettings,
  IconUserCircle
} from '@tabler/icons-react';
import { Link } from 'react-router-dom';

import { languages } from '../../contexts/LanguageContext';
import { doClassicLogout } from '../../functions/auth';
import { InvenTreeStyle } from '../../globalStyle';
import { useServerApiState } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';
import { PlaceholderPill } from '../items/Placeholder';

export function MainMenu() {
  const { classes, theme } = InvenTreeStyle();
  const [username] = useServerApiState((state) => [state.user?.name]);
  const [locale] = useLocalState((state) => [state.language]);

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
    <Menu width={260} position="bottom-end">
      <Menu.Target>
        <UnstyledButton className={classes.layoutHeaderUser}>
          <Group spacing={7}>
            <Text weight={500} size="sm" sx={{ lineHeight: 1 }} mr={3}>
              {username ? (
                username
              ) : (
                <Skeleton height={20} width={40} radius={theme.defaultRadius} />
              )}
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
  );
}
