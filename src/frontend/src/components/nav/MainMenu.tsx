import { Trans } from '@lingui/macro';
import {
  Group,
  Menu,
  Skeleton,
  Text,
  UnstyledButton,
  useMantineColorScheme
} from '@mantine/core';
import {
  IconChevronDown,
  IconLogout,
  IconMoonStars,
  IconSettings,
  IconSun,
  IconUserBolt,
  IconUserCog
} from '@tabler/icons-react';
import { Link, useNavigate } from 'react-router-dom';

import { doLogout } from '../../functions/auth';
import * as classes from '../../main.css';
import { useUserState } from '../../states/UserState';
import { vars } from '../../theme';

export function MainMenu() {
  const navigate = useNavigate();
  const [user, username] = useUserState((state) => [
    state.user,
    state.username
  ]);
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();

  return (
    <Menu width={260} position='bottom-end'>
      <Menu.Target>
        <UnstyledButton className={classes.layoutHeaderUser}>
          <Group gap={7}>
            {username() ? (
              <Text fw={500} size='sm' style={{ lineHeight: 1 }} mr={3}>
                {username()}
              </Text>
            ) : (
              <Skeleton height={20} width={40} radius={vars.radiusDefault} />
            )}
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
          to='/settings/user'
        >
          <Trans>Account Settings</Trans>
        </Menu.Item>
        {user?.is_staff && (
          <Menu.Item
            leftSection={<IconSettings />}
            component={Link}
            to='/settings/system'
          >
            <Trans>System Settings</Trans>
          </Menu.Item>
        )}
        <Menu.Item
          onClick={toggleColorScheme}
          leftSection={colorScheme === 'dark' ? <IconSun /> : <IconMoonStars />}
          c={
            colorScheme === 'dark' ? vars.colors.yellow[4] : vars.colors.blue[6]
          }
        >
          <Trans>Change Color Mode</Trans>
        </Menu.Item>
        {user?.is_staff && <Menu.Divider />}
        {user?.is_staff && (
          <Menu.Item
            leftSection={<IconUserBolt />}
            component={Link}
            to='/settings/admin'
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
