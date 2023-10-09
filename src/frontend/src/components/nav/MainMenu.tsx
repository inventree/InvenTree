import { Trans } from '@lingui/macro';
import { Group, Menu, Skeleton, Text, UnstyledButton } from '@mantine/core';
import {
  IconChevronDown,
  IconHeart,
  IconLogout,
  IconPlugConnected,
  IconSettings,
  IconUserCircle,
  IconUserCog
} from '@tabler/icons-react';
import { useContext } from 'react';
import { Link } from 'react-router-dom';

import { UserContext } from '../../contexts/UserContext';
import { doClassicLogout } from '../../functions/auth';
import { InvenTreeStyle } from '../../globalStyle';

export function MainMenu() {
  const { classes, theme } = InvenTreeStyle();

  const user = useContext(UserContext);

  return (
    <Menu width={260} position="bottom-end">
      <Menu.Target>
        <UnstyledButton className={classes.layoutHeaderUser}>
          <Group spacing={7}>
            <IconChevronDown />
          </Group>
        </UnstyledButton>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Label>
          <Trans>Settings</Trans>
        </Menu.Label>
        {user && (
          <Menu.Item
            icon={<IconUserCog />}
            component={Link}
            to="/settings/user"
          >
            <Trans>Account settings</Trans>
          </Menu.Item>
        )}
        {user?.is_staff && (
          <Menu.Item icon={<IconSettings />} component={Link} to="/settings/">
            <Trans>System Settings</Trans>
          </Menu.Item>
        )}
        {user?.is_staff && (
          <Menu.Item
            icon={<IconPlugConnected />}
            component={Link}
            to="/settings/plugin"
          >
            <Trans>Plugins</Trans>
          </Menu.Item>
        )}
        <Menu.Divider />
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
