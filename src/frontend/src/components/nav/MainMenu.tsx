import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { AuthContext } from '@lib/types/Auth';
import { Trans } from '@lingui/react/macro';
import {
  Button,
  Group,
  HoverCard,
  List,
  Menu,
  Skeleton,
  Table,
  Text,
  UnstyledButton,
  useMantineColorScheme
} from '@mantine/core';
import {
  IconChevronDown,
  IconInfoCircle,
  IconLogout,
  IconMoonStars,
  IconSettings,
  IconSun,
  IconUserBolt,
  IconUserCog
} from '@tabler/icons-react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi, doLogout } from '../../functions/auth';

import { useShallow } from 'zustand/react/shallow';
import * as classes from '../../main.css';
import { parseDate } from '../../pages/Index/Settings/AccountSettings/SecurityContent';
import { useServerApiState } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { ServerAPIProps } from '../../states/states';
import { vars } from '../../theme';
export function MainMenu() {
  const navigate = useNavigate();
  const [user, username] = useUserState(
    useShallow((state) => [state.user, state.username])
  );
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  const [server, auth_context] = useServerApiState((state) => [
    state.server,
    state.auth_context
  ]);

  return (
    <>
      {user?.is_superuser && (
        <HoverCard shadow='md' openDelay={500} closeDelay={500} withArrow>
          <HoverCard.Target>
            <IconInfoCircle />
          </HoverCard.Target>
          <HoverCard.Dropdown>
            <AuthContextInformation
              server={server}
              auth_context={auth_context}
            />
          </HoverCard.Dropdown>
        </HoverCard>
      )}

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
            leftSection={
              colorScheme === 'dark' ? <IconSun /> : <IconMoonStars />
            }
            c={
              colorScheme === 'dark'
                ? vars.colors.yellow[4]
                : vars.colors.blue[6]
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
    </>
  );
}
function AuthContextInformation({
  server,
  auth_context
}: Readonly<{
  server: ServerAPIProps;
  auth_context: AuthContext | undefined;
}>) {
  const [setAuthContext] = useServerApiState((state) => [state.setAuthContext]);

  function fetchAuthContext() {
    authApi(apiUrl(ApiEndpoints.auth_session)).then((resp) => {
      setAuthContext(resp.data.data);
    });
  }

  const rows = [
    { name: 'Server version', value: server.version },
    { name: 'API version', value: server.apiVersion },
    { name: 'User ID', value: auth_context?.user?.id }
  ];
  return (
    <>
      <Table>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>
              <Trans>Name</Trans>
            </Table.Th>
            <Table.Th>
              <Trans>Value</Trans>
            </Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {rows.map((element) => (
            <Table.Tr key={element.name}>
              <Table.Td>{element.name}</Table.Td>
              <Table.Td>{element.value}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
      {auth_context?.methods && (
        <>
          <Text size='sm'>
            <Trans>Methods</Trans>
          </Text>

          <List type='ordered'>
            {auth_context?.methods.map((method: any) => (
              <List.Item key={method.at}>
                <strong>{parseDate(method.at)}</strong>: {method.method}
              </List.Item>
            ))}
          </List>
        </>
      )}
      <Button
        variant='light'
        size='compact-md'
        onClick={(e) => {
          e.preventDefault();
          fetchAuthContext();
        }}
      >
        <Trans>Reload</Trans>
      </Button>
    </>
  );
}
