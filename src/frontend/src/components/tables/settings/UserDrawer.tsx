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
import { useToggle } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { IconCheck } from '@tabler/icons-react';
import { useEffect, useState } from 'react';

import { api } from '../../../App';
import { ApiPaths } from '../../../enums/ApiEndpoints';
import {
  invalidResponse,
  permissionDenied
} from '../../../functions/notifications';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { EditButton } from '../../items/EditButton';
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
  const [user] = useUserState((state) => [state.user]);
  const [rightsValue, setRightsValue] = useState(['']);
  const [locked, setLocked] = useState<boolean>(false);
  const [userEditing, setUserEditing] = useToggle([false, true] as const);

  // Set initial values
  useEffect(() => {
    if (!userDetail) return;

    setLocked(true);
    // rights
    let new_rights = [];
    if (userDetail.is_staff) {
      new_rights.push('is_staff');
    }
    if (userDetail.is_active) {
      new_rights.push('is_active');
    }
    if (userDetail.is_superuser) {
      new_rights.push('is_superuser');
    }
    setRightsValue(new_rights);

    setLocked(false);
  }, [userDetail]);

  // actions on role change
  function changeRights(roles: [string]) {
    if (!userDetail) return;

    let data = {
      is_staff: roles.includes('is_staff'),
      is_superuser: roles.includes('is_superuser')
    };
    if (
      data.is_staff != userDetail.is_staff ||
      data.is_superuser != userDetail.is_superuser
    ) {
      setPermission(userDetail.pk, data);
    }
    if (userDetail.is_active != roles.includes('is_active')) {
      setActive(userDetail.pk, roles.includes('is_active'));
    }
    setRightsValue(roles);
  }

  function setPermission(pk: number, data: any) {
    setLocked(true);
    api
      .patch(apiUrl(ApiPaths.user_list, pk), data)
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
      })
      .finally(() => setLocked(false));
  }

  function setActive(pk: number, active: boolean) {
    setLocked(true);
    api
      .patch(apiUrl(ApiPaths.user_list, pk), {
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
      })
      .finally(() => setLocked(false));
  }

  const userEditable = locked || !userEditing;
  return (
    <Drawer
      opened={opened}
      onClose={close}
      position="right"
      title={userDetail ? t`User details for ${userDetail.username}` : ''}
      overlayProps={{ opacity: 0.5, blur: 4 }}
    >
      <Stack spacing={'xs'}>
        <Group>
          <Title order={5}>
            <Trans>Details</Trans>
          </Title>
          <EditButton
            editing={userEditing}
            setEditing={setUserEditing}
            disabled
          />
        </Group>
        {userDetail ? (
          <Stack spacing={0} ml={'md'}>
            <TextInput
              label={t`Username`}
              value={userDetail.username}
              disabled={userEditable}
            />
            <TextInput label={t`Email`} value={userDetail.email} disabled />
            <TextInput
              label={t`First Name`}
              value={userDetail.first_name}
              disabled={userEditable}
            />
            <TextInput
              label={t`Last Name`}
              value={userDetail.last_name}
              disabled={userEditable}
            />

            <Text>
              <Trans>Rights</Trans>
            </Text>
            <Chip.Group multiple value={rightsValue} onChange={changeRights}>
              <Group spacing={0}>
                <Chip value="is_active" disabled={locked || !user?.is_staff}>
                  <Trans>Active</Trans>
                </Chip>
                <Chip value="is_staff" disabled={locked || !user?.is_staff}>
                  <Trans>Staff</Trans>
                </Chip>
                <Chip
                  value="is_superuser"
                  disabled={locked || !(user?.is_staff && user?.is_superuser)}
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
      </Stack>
    </Drawer>
  );
}
