import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Accordion, Alert, LoadingOverlay, Stack, Text } from '@mantine/core';
import {
  IconInfoCircle,
  IconKey,
  IconLock,
  IconLockOpen,
  IconUserCircle
} from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl } from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { showNotification } from '@mantine/notifications';
import { useNavigate } from 'react-router-dom';
import { useShallow } from 'zustand/react/shallow';
import { api } from '../../App';
import { EditApiForm } from '../../components/forms/ApiForm';
import { StylishText } from '../../components/items/StylishText';
import {
  TransferList,
  type TransferListItem
} from '../../components/items/TransferList';
import { DetailDrawer } from '../../components/nav/DetailDrawer';
import { showApiErrorMessage } from '../../functions/notifications';
import {
  useApiFormModal,
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { BooleanColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import type { GroupDetailI } from './GroupTable';

export interface UserDetailI {
  pk: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  groups: GroupDetailI[];
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
}

export function UserDrawer({
  id,
  refreshTable
}: Readonly<{
  id: string;
  refreshTable: () => void;
}>) {
  const {
    instance: userDetail,
    refreshInstance,
    instanceQuery: { isFetching, error }
  } = useInstance<UserDetailI>({
    endpoint: ApiEndpoints.user_list,
    pk: id
  });

  const currentUserPk = useUserState(useShallow((s) => s.user?.pk));
  const isCurrentUser = useMemo(
    () => currentUserPk === Number.parseInt(id, 10),
    [currentUserPk, id]
  );

  const userGroups = useInstance({
    endpoint: ApiEndpoints.group_list,
    hasPrimaryKey: false,
    defaultValue: []
  });

  const availableGroups: TransferListItem[] = useMemo(() => {
    return (
      userGroups.instance?.map((group: any) => {
        return {
          value: group.pk,
          label: group.name
        };
      }) ?? []
    );
  }, [userGroups.instance]);

  const selectedGroups: TransferListItem[] = useMemo(() => {
    return (
      userDetail?.groups?.map((group: any) => {
        return {
          value: group.pk,
          label: group.name
        };
      }) ?? []
    );
  }, [userDetail]);

  const onSaveGroups = useCallback(
    (selected: TransferListItem[]) => {
      if (!userDetail.pk) {
        return;
      }
      api
        .patch(apiUrl(ApiEndpoints.user_list, userDetail.pk), {
          group_ids: selected.map((group) => group.value)
        })
        .then(() => {
          showNotification({
            title: t`Groups updated`,
            message: t`User groups updated successfully`,
            color: 'green'
          });
        })
        .catch((error) => {
          showApiErrorMessage({
            error: error,
            title: t`Error updating user groups`
          });
        })
        .finally(() => {
          refreshInstance();
          refreshTable();
        });
    },
    [userDetail]
  );

  if (isFetching) {
    return <LoadingOverlay visible={true} />;
  }

  if (error) {
    return (
      <Text>
        {(error as any)?.response?.status === 404 ? (
          <Trans>User with id {id} not found</Trans>
        ) : (
          <Trans>An error occurred while fetching user details</Trans>
        )}
      </Text>
    );
  }

  return (
    <Stack gap='xs'>
      <Accordion defaultValue={'details'}>
        <Accordion.Item key='details' value='details'>
          <Accordion.Control>
            <StylishText size='lg'>
              <Trans>User Details</Trans>
            </StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <EditApiForm
              props={{
                url: ApiEndpoints.user_list,
                pk: id,
                fields: {
                  username: {},
                  first_name: {},
                  last_name: {},
                  email: {},
                  is_active: {
                    label: t`Is Active`,
                    description: t`Designates whether this user should be treated as active. Unselect this instead of deleting accounts.`,
                    disabled: isCurrentUser
                  },
                  is_staff: {
                    label: t`Is Staff`,
                    description: t`Designates whether the user can log into the django admin site.`,
                    disabled: isCurrentUser
                  },
                  is_superuser: {
                    label: t`Is Superuser`,
                    description: t`Designates that this user has all permissions without explicitly assigning them.`,
                    disabled: isCurrentUser
                  }
                },
                postFormContent: isCurrentUser ? (
                  <Alert
                    title={<Trans>Info</Trans>}
                    color='blue'
                    icon={<IconInfoCircle />}
                  >
                    <Trans>
                      You cannot edit the rights for the currently logged-in
                      user.
                    </Trans>
                  </Alert>
                ) : undefined,
                onFormSuccess: () => {
                  refreshTable();
                  refreshInstance();
                }
              }}
              id={`user-detail-drawer-${id}`}
            />
          </Accordion.Panel>
        </Accordion.Item>

        <Accordion.Item key='groups' value='groups'>
          <Accordion.Control>
            <StylishText size='lg'>
              <Trans>User Groups</Trans>
            </StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <TransferList
              available={availableGroups}
              selected={selectedGroups}
              onSave={onSaveGroups}
            />
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </Stack>
  );
}

/**
 * Table for displaying list of users
 */
export function UserTable({
  directLink
}: Readonly<{
  directLink?: boolean;
}>) {
  const table = useTable('users');
  const navigate = useNavigate();
  const user = useUserState();

  const openDetailDrawer = useCallback(
    (pk: number) => {
      if (user.hasChangePermission(ModelType.user)) {
        navigate(`user-${pk}/`);
      }
    },
    [user]
  );

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'username',
        sortable: true,
        switchable: false
      },
      {
        accessor: 'first_name',
        sortable: true
      },
      {
        accessor: 'last_name',
        sortable: true
      },
      {
        accessor: 'email',
        sortable: true
      },
      {
        accessor: 'groups',
        title: t`Groups`,
        sortable: true,
        switchable: true,
        render: (record: any) => {
          return record.groups.length;
        }
      },
      BooleanColumn({
        accessor: 'is_staff'
      }),
      BooleanColumn({
        accessor: 'is_superuser'
      }),
      BooleanColumn({
        accessor: 'is_active'
      })
    ];
  }, []);

  // Row Actions
  const [selectedUser, setSelectedUser] = useState<number>(-1);

  const rowActions = useCallback(
    (record: UserDetailI): RowAction[] => {
      const staff: boolean = user.isStaff() || user.isSuperuser();
      return [
        RowEditAction({
          onClick: () => openDetailDrawer(record.pk),
          hidden: !staff || !user.hasChangePermission(ModelType.user)
        }),
        RowDeleteAction({
          hidden: !staff || !user.hasDeletePermission(ModelType.user),
          onClick: () => {
            setSelectedUser(record.pk);
            deleteUser.open();
          }
        }),
        {
          icon: <IconUserCircle />,
          title: t`Open Profile`,
          onClick: () => {
            navigate(getDetailUrl(ModelType.user, record.pk));
          }
        },
        {
          icon: <IconKey />,
          title: t`Change Password`,
          color: 'blue',
          onClick: () => {
            setSelectedUser(record.pk);
            setPassword.open();
          },
          hidden: !user.isSuperuser()
        },
        {
          icon: <IconLock />,
          title: t`Lock user`,
          color: 'blue',
          onClick: () => {
            setUserActiveState(record.pk, false);
            table.refreshTable();
          },
          hidden: !record.is_active
        },
        {
          icon: <IconLockOpen />,
          title: t`Unlock user`,
          color: 'blue',
          onClick: () => {
            setUserActiveState(record.pk, true);
            table.refreshTable();
          },
          hidden: record.is_active
        }
      ];
    },
    [user]
  );

  const deleteUser = useDeleteApiFormModal({
    url: ApiEndpoints.user_list,
    pk: selectedUser,
    title: t`Delete user`,
    successMessage: t`User deleted`,
    table: table,
    preFormWarning: t`Are you sure you want to delete this user?`
  });

  // Table Actions - Add New User
  const newUser = useCreateApiFormModal({
    url: ApiEndpoints.user_list,
    title: t`Add User`,
    fields: {
      username: {},
      email: {},
      first_name: {},
      last_name: {}
    },
    table: table,
    successMessage: t`Added user`
  });

  const setPassword = useApiFormModal({
    url: ApiEndpoints.user_set_password,
    method: 'PUT',
    pk: selectedUser,
    title: t`Set Password`,
    fields: {
      password: { field_type: 'password' },
      override_warning: {}
    },
    successMessage: t`Password updated`
  });

  const tableActions = useMemo(() => {
    const actions = [];
    const staff: boolean = user.isStaff() || user.isSuperuser();

    actions.push(
      <AddItemButton
        key='add-user'
        onClick={newUser.open}
        tooltip={t`Add user`}
        hidden={!staff || !user.hasAddPermission(ModelType.user)}
      />
    );

    return actions;
  }, [user]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'is_active',
        label: t`Active`,
        description: t`Show active users`
      },
      {
        name: 'is_staff',
        label: t`Staff`,
        description: t`Show staff users`
      },
      {
        name: 'is_superuser',
        label: t`Superuser`,
        description: t`Show superusers`
      }
    ];
  }, []);

  // Determine whether the UserTable is editable
  const editable: boolean = useMemo(
    () => !directLink && user.isStaff() && user.hasChangeRole(UserRoles.admin),
    [user, directLink]
  );

  return (
    <>
      {editable && setPassword.modal}
      {editable && newUser.modal}
      {editable && deleteUser.modal}
      {editable && (
        <DetailDrawer
          size='xl'
          title={t`Edit User`}
          renderContent={(id) => {
            if (!id || !id.startsWith('user-')) return false;
            return (
              <UserDrawer
                id={id.replace('user-', '')}
                refreshTable={table.refreshTable}
              />
            );
          }}
        />
      )}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.user_list)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: editable ? rowActions : undefined,
          tableActions: editable ? tableActions : undefined,
          tableFilters: tableFilters,
          onRowClick: editable
            ? (record) => openDetailDrawer(record.pk)
            : undefined,
          modelType: directLink ? ModelType.user : undefined
        }}
      />
    </>
  );
}

async function setUserActiveState(userId: number, active: boolean) {
  try {
    await api.patch(apiUrl(ApiEndpoints.user_list, userId), {
      is_active: active
    });
    showNotification({
      title: t`User updated`,
      message: t`User updated successfully`,
      color: 'green'
    });
  } catch (error) {
    showApiErrorMessage({
      error: error,
      title: t`Error updating user`
    });
  }
}
