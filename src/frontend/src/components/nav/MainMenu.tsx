import { Trans } from '@lingui/macro';
import { Group, Menu, Skeleton, Text, UnstyledButton } from '@mantine/core';
import {
  IconChevronDown,
  IconHeart,
  IconLogout,
  IconSettings,
  IconUserCircle
} from '@tabler/icons-react';
import { Link } from 'react-router-dom';

import { doClassicLogout } from '../../functions/auth';
import { InvenTreeStyle } from '../../globalStyle';
import { useApiState } from '../../states/ApiState';
import { PlaceholderPill } from '../items/Placeholder';

export function MainMenu() {
  const { classes, theme } = InvenTreeStyle();
  const [username] = useApiState((state) => [state.user?.name]);
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
        <Menu.Item icon={<IconUserCircle />}>
          <Trans>Profile</Trans> <PlaceholderPill />
        </Menu.Item>

        <Menu.Label>
          <Trans>Settings</Trans>
        </Menu.Label>
        <Menu.Item icon={<IconSettings />} component={Link} to="/profile/user">
          <Trans>Account settings</Trans>
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
