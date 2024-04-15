import { Trans } from '@lingui/macro';
import { Group, Menu, Skeleton, Text, UnstyledButton } from '@mantine/core';
import {
  IconChevronDown,
  IconLogout,
  IconSettings,
  IconUserBolt,
  IconUserCog
} from '@tabler/icons-react';
import { Link, useNavigate } from 'react-router-dom';

import { doLogout } from '../../functions/auth';
import * as classes from '../../main.css';
import { useUserState } from '../../states/UserState';
import { theme } from '../../theme';

export function MainMenu() {
  const navigate = useNavigate();
  const userState = useUserState();

  return (
    <Menu width={260} position="bottom-end">
      <Menu.Target>
        <UnstyledButton className={classes.layoutHeaderUser}>
          <Group gap={7}>
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
        <Menu.Item
          leftSection={<IconUserCog />}
          component={Link}
          to="/settings/user"
        >
          <Trans>Account settings</Trans>
        </Menu.Item>
        {userState.user?.is_staff && (
          <Menu.Item
            leftSection={<IconSettings />}
            component={Link}
            to="/settings/system"
          >
            <Trans>System Settings</Trans>
          </Menu.Item>
        )}
        {userState.user?.is_staff && <Menu.Divider />}
        {userState.user?.is_staff && (
          <Menu.Item
            leftSection={<IconUserBolt />}
            component={Link}
            to="/settings/admin"
          >
            <Trans>Admin Center</Trans>
          </Menu.Item>
        )}
        <Menu.Divider />
        <Menu.Item
          leftSection={<IconLogout />}
          onClick={() => {
            doLogout(navigate);
          }}
        >
          <Trans>Logout</Trans>
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  );
}
