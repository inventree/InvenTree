import { Trans, t } from '@lingui/macro';
import {
  Chip,
  Drawer,
  Group,
  List,
  Loader,
  Stack,
  Text,
  TextInput,
  Title
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCheck } from '@tabler/icons-react';
import { useEffect, useState } from 'react';

import { api } from '../../../App';
import {
  invalidResponse,
  permissionDenied
} from '../../../functions/notifications';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { UserDetailI } from './UserTable';

export function UserDrawer({
  opened,
  close,
  refreshTable,
  userDetail
}: {
  opened: boolean;
  close: () => void;
  refreshTable: () => void;
  userDetail: UserDetailI | undefined;
}) {
  const [value, setValue] = useState(['']);
  const [user] = useUserState((state) => [state.user]);

  // Set initial values
  useEffect(() => {
    if (!userDetail) return;
    let new_roles = [];
    if (userDetail.is_staff) {
      new_roles.push('is_staff');
    }
    if (userDetail.is_active) {
      new_roles.push('is_active');
    }
    if (userDetail.is_superuser) {
      new_roles.push('is_superuser');
    }
    setValue(new_roles);
  }, [userDetail]);

  // actions on role change
  function changeRole(roles: []) {
    if (!userDetail) return;

    let data = {
      is_staff: roles.includes('is_staff'),
      is_superuser: roles.includes('is_superuser')
    };
    if (
      data.is_staff != userDetail.is_staff ||
      data.is_superuser != userDetail.is_superuser
    ) {
      console.log('changing role state for user');
      setPermission(userDetail.pk, data);
    }
    if (userDetail.is_active != roles.includes('is_active')) {
      console.log('changing active state for user');
      setActive(userDetail.pk, roles.includes('is_active'));
    }
    setValue(roles);
  }

  function setPermission(pk: number, data: any) {
    api
      .patch(`${apiUrl(ApiPaths.user_list)}${pk}/`, data)
      .then(() => {
        notifications.show({
          title: t`User permission changed successfully`,
          message: t`Some changes might only take effect after the user refreshes their login.`,
          color: 'green',
          icon: <IconCheck size="1rem" />
        });
        refreshTable();
      })
      .catch((error) => {
        if (error.response.status === 403) {
          permissionDenied();
        } else {
          console.log(error);
          invalidResponse(error.response.status);
        }
      });
  }

  function setActive(pk: number, active: boolean) {
    api
      .patch(`${apiUrl(ApiPaths.user_list)}${pk}/`, {
        is_active: active
      })
      .then(() => {
        notifications.show({
          title: t`Changed user active status successfully`,
          message: t`Set to ${active}`,
          color: 'green',
          icon: <IconCheck size="1rem" />
        });
        refreshTable();
      })
      .catch((error) => {
        if (error.response.status === 403) {
          permissionDenied();
        } else {
          console.log(error);
          invalidResponse(error.response.status);
        }
      });
  }

  return (
    <Drawer
      opened={opened}
      onClose={close}
      position="right"
      title={userDetail ? t`User details for ${userDetail.username}` : ''}
      overlayProps={{ opacity: 0.5, blur: 4 }}
    >
      <Stack spacing={'xs'}>
        <Title order={5}>
          <Trans>Details</Trans>
        </Title>
        {userDetail ? (
          <Stack spacing={0} ml={'md'}>
            <TextInput
              label={t`Username`}
              value={userDetail.username}
              disabled
            />
            <TextInput label={t`Email`} value={userDetail.email} disabled />
            <TextInput
              label={t`First Name`}
              value={userDetail.first_name}
              disabled
            />
            <TextInput
              label={t`Last Name`}
              value={userDetail.last_name}
              disabled
            />

            <Text>
              <Trans>Roles</Trans>
            </Text>
            <Chip.Group multiple value={value} onChange={changeRole}>
              <Group spacing={0}>
                <Chip value="is_active" disabled={!user?.is_staff}>
                  <Trans>Active</Trans>
                </Chip>
                <Chip value="is_staff" disabled={!user?.is_staff}>
                  <Trans>Staff</Trans>
                </Chip>
                <Chip
                  value="is_superuser"
                  disabled={!(user?.is_staff && user?.is_superuser)}
                >
                  <Trans>Superuser</Trans>
                </Chip>
              </Group>
            </Chip.Group>
          </Stack>
        ) : (
          <Loader />
        )}

        <Title order={5}>
          <Trans>Groups</Trans>
        </Title>
        <Text ml={'md'}>
          {userDetail && userDetail.groups.length == 0 ? (
            <Trans>No groups</Trans>
          ) : (
            <List>
              {userDetail &&
                userDetail.groups.map((message) => (
                  <List.Item key={message.name}>{message.name}</List.Item>
                ))}
            </List>
          )}
        </Text>
        <Title order={5}>
          <Trans>Roles</Trans>
        </Title>
      </Stack>
    </Drawer>
  );
}
