import { Trans, t } from '@lingui/macro';
import { Badge, Group, Stack, Table } from '@mantine/core';
import { IconEdit, IconKey, IconUser } from '@tabler/icons-react';
import { useMemo } from 'react';

import { ActionButton, StylishText } from '@lib/components';
import { ActionDropdown } from '@lib/components';
import { YesNoUndefinedButton } from '@lib/components/buttons/YesNoButton';
import { ApiEndpoints } from '@lib/core';
import type { ApiFormFieldSet } from '@lib/forms';
import { useEditApiFormModal } from '@lib/forms';
import { useUserState } from '@lib/states';
import { useNavigate } from 'react-router-dom';

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

  const editAccount = useEditApiFormModal({
    title: t`Edit Account Information`,
    url: ApiEndpoints.user_me,
    onFormSuccess: fetchUserState,
    fields: userFields,
    successMessage: t`Account details updated`
  });

  const profileFields: ApiFormFieldSet = useMemo(() => {
    return {
      displayname: {},
      position: {},
      status: {},
      location: {},
      active: {},
      contact: {},
      type: {},
      organisation: {},
      primary_group: {}
    };
  }, []);

  const editProfile = useEditApiFormModal({
    title: t`Edit Profile Information`,
    url: ApiEndpoints.user_profile,
    onFormSuccess: fetchUserState,
    fields: profileFields,
    successMessage: t`Profile details updated`
  });

  const accountDetailFields = useMemo(
    () => [
      { label: t`Username`, value: user?.username },
      { label: t`First Name`, value: user?.first_name },
      { label: t`Last Name`, value: user?.last_name },
      {
        label: t`Staff Access`,
        value: <YesNoUndefinedButton value={user?.is_staff} />
      },
      {
        label: t`Superuser`,
        value: <YesNoUndefinedButton value={user?.is_superuser} />
      }
    ],
    [user]
  );

  const profileDetailFields = useMemo(
    () => [
      { label: t`Display Name`, value: user?.profile?.displayname },
      { label: t`Position`, value: user?.profile?.position },
      { label: t`Status`, value: user?.profile?.status },
      { label: t`Location`, value: user?.profile?.location },
      {
        label: t`Active`,
        value: <YesNoUndefinedButton value={user?.profile?.active} />
      },
      { label: t`Contact`, value: user?.profile?.contact },
      { label: t`Type`, value: <Badge>{user?.profile?.type}</Badge> },
      { label: t`Organisation`, value: user?.profile?.organisation },
      { label: t`Primary Group`, value: user?.profile?.primary_group }
    ],
    [user]
  );

  return (
    <>
      {editAccount.modal}
      {editProfile.modal}
      <Stack gap='xs'>
        <Group justify='space-between'>
          <StylishText size='lg'>
            <Trans>Account Details</Trans>
          </StylishText>
          <ActionDropdown
            tooltip={t`Account Actions`}
            icon={<IconUser />}
            actions={[
              {
                name: t`Edit Account`,
                icon: <IconEdit />,
                tooltip: t`Edit Account Information`,
                onClick: editAccount.open
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
        {renderDetailTable(accountDetailFields)}

        <Group justify='space-between'>
          <StylishText size='lg'>
            <Trans>Profile Details</Trans>
          </StylishText>
          <ActionButton
            text={t`Edit Profile`}
            icon={<IconEdit />}
            tooltip={t`Edit Profile Information`}
            onClick={editProfile.open}
            variant='light'
          />
        </Group>
        {renderDetailTable(profileDetailFields)}
      </Stack>
    </>
  );

  function renderDetailTable(data: { label: string; value: any }[]) {
    return (
      <Table>
        <Table.Tbody>
          {data.map((item) => (
            <Table.Tr key={item.label}>
              <Table.Td>
                <Trans>{item.label}</Trans>
              </Table.Td>
              <Table.Td>{item.value}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    );
  }
}
