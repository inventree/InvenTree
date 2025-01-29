import { Trans, t } from '@lingui/macro';
import {
  Alert,
  List,
  LoadingOverlay,
  Spoiler,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { EditApiForm } from '../../components/forms/ApiForm';
import {
  DetailDrawer,
  DetailDrawerLink
} from '../../components/nav/DetailDrawer';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import { BooleanColumn } from '../ColumnRenderers';
import type { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction, RowEditAction } from '../RowActions';
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
    pk: id,
    throwError: true
  });

  const currentUserPk = useUserState((s) => s.user?.pk);
  const isCurrentUser = useMemo(
    () => currentUserPk === Number.parseInt(id, 10),
    [currentUserPk, id]
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
    <Stack>
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
                You cannot edit the rights for the currently logged-in user.
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

      <Stack>
        <Title order={5}>
          <Trans>Groups</Trans>
        </Title>
        <Spoiler maxHeight={125} showLabel='Show More' hideLabel='Show Less'>
          <Text ml={'md'}>
            {userDetail?.groups && userDetail?.groups?.length > 0 ? (
              <List>
                {userDetail?.groups?.map((group: any) => (
                  <List.Item key={group.pk}>
                    <DetailDrawerLink
                      to={`../group-${group.pk}`}
                      text={group.name}
                    />
                  </List.Item>
                ))}
              </List>
            ) : (
              <Trans>No groups</Trans>
            )}
          </Text>
        </Spoiler>
      </Stack>
    </Stack>
  );
}

/**
 * Table for displaying list of users
 */
export function UserTable() {
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
      return [
        RowEditAction({
          onClick: () => openDetailDrawer(record.pk),
          hidden: !user.hasChangePermission(ModelType.user)
        }),
        RowDeleteAction({
          hidden: !user.hasDeletePermission(ModelType.user),
          onClick: () => {
            setSelectedUser(record.pk);
            deleteUser.open();
          }
        })
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
    title: t`Add user`,
    fields: {
      username: {},
      email: {},
      first_name: {},
      last_name: {}
    },
    table: table,
    successMessage: t`Added user`
  });

  const tableActions = useMemo(() => {
    const actions = [];

    actions.push(
      <AddItemButton
        key='add-user'
        onClick={newUser.open}
        tooltip={t`Add user`}
        hidden={!user.hasAddPermission(ModelType.user)}
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

  return (
    <>
      {newUser.modal}
      {deleteUser.modal}
      <DetailDrawer
        title={t`Edit user`}
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
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.user_list)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions,
          tableFilters: tableFilters,
          onRowClick: (record) => openDetailDrawer(record.pk)
        }}
      />
    </>
  );
}
