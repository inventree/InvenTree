import { Trans, t } from '@lingui/macro';
import {
  ActionIcon,
  Button,
  Group,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
  Tooltip
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useToggle } from '@mantine/hooks';
import { IconEdit } from '@tabler/icons-react';
import { useMemo } from 'react';

import { api } from '../../../../App';
import { EditButton } from '../../../../components/buttons/EditButton';
import { ApiFormFieldSet } from '../../../../components/forms/fields/ApiFormField';
import { StylishText } from '../../../../components/items/StylishText';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { useEditApiFormModal } from '../../../../hooks/UseForm';
import { apiUrl } from '../../../../states/ApiState';
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
          <StylishText size="xl">
            <Trans>User Details</Trans>
          </StylishText>
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
