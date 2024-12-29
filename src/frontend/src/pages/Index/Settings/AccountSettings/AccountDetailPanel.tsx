import { Trans, t } from '@lingui/macro';
import { Group, Stack, Table, Title } from '@mantine/core';
import { IconKey, IconUser } from '@tabler/icons-react';
import { useMemo } from 'react';

import { useNavigate } from 'react-router-dom';
import { YesNoUndefinedButton } from '../../../../components/buttons/YesNoButton';
import type { ApiFormFieldSet } from '../../../../components/forms/fields/ApiFormField';
import { ActionDropdown } from '../../../../components/items/ActionDropdown';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { useEditApiFormModal } from '../../../../hooks/UseForm';
import { useUserState } from '../../../../states/UserState';

export function AccountDetailPanel() {
  const navigate = useNavigate();

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
      <Stack gap='xs'>
        <Group justify='space-between'>
          <Title order={3}>
            <Trans>User Details</Trans>
          </Title>
          <ActionDropdown
            tooltip={t`User Actions`}
            icon={<IconUser />}
            actions={[
              {
                name: t`Edit User`,
                icon: <IconUser />,
                tooltip: t`Edit User Information`,
                onClick: editUser.open
              },
              {
                name: t`Change Password`,
                icon: <IconKey />,
                tooltip: t`Change User Password`,
                onClick: () => {
                  navigate('/change-password');
                }
              }
            ]}
          />
        </Group>

        <Table>
          <Table.Tbody>
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
            <Table.Tr>
              <Table.Td>
                <Trans>Staff Access</Trans>
              </Table.Td>
              <Table.Td>
                <YesNoUndefinedButton value={user?.is_staff} />
              </Table.Td>
            </Table.Tr>
            <Table.Tr>
              <Table.Td>
                <Trans>Superuser</Trans>
              </Table.Td>
              <Table.Td>
                <YesNoUndefinedButton value={user?.is_superuser} />
              </Table.Td>
            </Table.Tr>
          </Table.Tbody>
        </Table>
      </Stack>
    </>
  );
}
