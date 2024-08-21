import { Trans, t } from '@lingui/macro';
import { ActionIcon, Group, Stack, Table, Title, Tooltip } from '@mantine/core';
import { IconEdit } from '@tabler/icons-react';
import { useMemo } from 'react';

import { ApiFormFieldSet } from '../../../../components/forms/fields/ApiFormField';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
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
          <Tooltip label={t`Edit User Information`}>
            <ActionIcon variant="default" onClick={editUser.open}>
              <IconEdit />
            </ActionIcon>
          </Tooltip>
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
