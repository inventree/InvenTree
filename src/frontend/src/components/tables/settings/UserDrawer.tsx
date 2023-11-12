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
import { useEffect, useState } from 'react';

import { useUserState } from '../../../states/UserState';

export function UserDrawer({
  opened,
  close,
  userDetail
}: {
  opened: boolean;
  close: () => void;
  userDetail: {} | undefined;
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
  function changeRole(roles) {
    // Todo submit to backend
    console.log('would change roles to ', roles);
    setValue(roles);
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
                  <List.Item key={message}>{message.name}</List.Item>
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
