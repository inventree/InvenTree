import { Trans, t } from '@lingui/macro';
import { ActionIcon, Group, Stack, Table, Title, Tooltip } from '@mantine/core';
import { IconDots, IconEdit, IconKey, IconUser } from '@tabler/icons-react';
import { useMemo } from 'react';

import { ApiFormFieldSet } from '../../../../components/forms/fields/ApiFormField';
import { ActionDropdown } from '../../../../components/items/ActionDropdown';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { notYetImplemented } from '../../../../functions/notifications';
import { useEditApiFormModal } from '../../../../hooks/UseForm';
import { useUserState } from '../../../../states/UserState';

export function AccountDetailPanel() {
  const [user, fetchUserState] = useUserState((state) => [
    state.user,
    state.fetchUserState
  ]);

  const userFields: ApiFormFieldSet = useMemo(() => {
    return {
      first_name: {},
      last_name: {}
    };
  }, []);

  const editUser = useEditApiFormModal({
    title: t`Edit User Information`,
    url: ApiEndpoints.user_me,
    onFormSuccess: fetchUserState,
    fields: userFields,
    successMessage: t`User details updated`
  });

  return (
    <>
      {editUser.modal}
      <Stack gap="xs">
        <Group justify="space-between">
          <Title order={3}>
            <Trans>User Details</Trans>
          </Title>
          <ActionDropdown
            tooltip={t`User Actions`}
            icon={<IconDots />}
            actions={[
              {
                name: t`Edit User`,
                icon: <IconUser />,
                tooltip: t`Edit User Information`,
                onClick: editUser.open
              },
              {
                name: t`Set Password`,
                icon: <IconKey />,
                tooltip: t`Set User Password`,
                onClick: notYetImplemented
              }
            ]}
          />
        </Group>
        <Table>
          <Table.Tr>
            <Table.Td>
              <Trans>Username</Trans>
            </Table.Td>
            <Table.Td>{user?.username}</Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>First Name</Trans>
            </Table.Td>
            <Table.Td>{user?.first_name}</Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Last Name</Trans>
            </Table.Td>
            <Table.Td>{user?.last_name}</Table.Td>
          </Table.Tr>
        </Table>
      </Stack>
    </>
  );
}
