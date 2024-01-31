import { Trans } from '@lingui/macro';
import { Group, Menu, Skeleton, Text, UnstyledButton } from '@mantine/core';
import {
  IconChevronDown,
  IconLogout,
  IconSettings,
  IconUserBolt,
  IconUserCog
} from '@tabler/icons-react';
import { Link } from 'react-router-dom';

import { doClasssicLogout } from '../../functions/auth';
import { InvenTreeStyle } from '../../globalStyle';
import { useUserState } from '../../states/UserState';

export function MainMenu() {
  const { classes, theme } = InvenTreeStyle();
  const userState = useUserState();

  return (
    <Menu width={260} position="bottom-end">
      <Menu.Target>
        <UnstyledButton className={classes.layoutHeaderUser}>
          <Group spacing={7}>
            <Text weight={500} size="sm" sx={{ lineHeight: 1 }} mr={3}>
              {userState.username() ? (
                userState.username()
              ) : (
                <Skeleton height={20} width={40} radius={theme.defaultRadius} />
              )}
            </Text>
            <IconChevronDown />
          </Group>
        </UnstyledButton>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Label>
          <Trans>Settings</Trans>
        </Menu.Label>
        <Menu.Item icon={<IconUserCog />} component={Link} to="/settings/user">
          <Trans>Account settings</Trans>
        </Menu.Item>
        {userState.user?.is_staff && (
          <Menu.Item
            icon={<IconSettings />}
            component={Link}
            to="/settings/system"
          >
            <Trans>System Settings</Trans>
          </Menu.Item>
        )}
        {userState.user?.is_staff && <Menu.Divider />}
        {userState.user?.is_staff && (
          <Menu.Item
            icon={<IconUserBolt />}
            component={Link}
            to="/settings/admin"
          >
            <Trans>Admin Center</Trans>
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
