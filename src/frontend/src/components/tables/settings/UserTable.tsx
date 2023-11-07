import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { useCallback, useMemo } from 'react';

import {
  openCreateApiForm,
  openDeleteApiForm,
  openEditApiForm
} from '../../../functions/forms';
import { InvenTreeStyle } from '../../../globalStyle';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { AddItemButton } from '../../buttons/AddItemButton';
import { TableColumn } from '../Column';
import { BooleanColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

enum UserRole {
  REGULAR = 'regular',
  STAFF = 'staff',
  SUPERUSER = 'superuser'
}

/**
 * Table for displaying list of users
 */
export function UserTable() {
  const { tableKey, refreshTable } = useTableRefresh('users');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'email',
        sortable: true,
        title: t`Email`
      },
      {
        accessor: 'username',
        sortable: true,
        switchable: false,
        title: t`Username`
      },
      {
        accessor: 'first_name',
        sortable: true,
        title: t`First Name`
      },
      {
        accessor: 'last_name',
        sortable: true,
        title: t`Last Name`
      },
      BooleanColumn({
        accessor: 'is_staff',
        title: t`Staff`
      }),
      BooleanColumn({
        accessor: 'is_superuser',
        title: t`Superuser`
      }),
      BooleanColumn({
        accessor: 'is_active',
        title: t`Active`
      })
    ];
  }, []);

  const rowActions = useCallback((record: any): RowAction[] => {
    const [user] = useUserState((state) => [state.user]);
    const { theme } = InvenTreeStyle();

    function setPermission(pk: number, new_role: UserRole) {
      /* TODO - implement */
      console.log(new_role);
    }

    return [
      {
        title: t`Make regular user`,
        color: theme.colorScheme === 'dark' ? theme.white : theme.black,
        onClick: () => {
          setPermission(record.pk, UserRole.REGULAR);
        },
        hidden: !user?.is_staff || !(record.is_superuser && record.is_staff)
      },
      {
        title: t`Make staff user`,
        color: theme.colorScheme === 'dark' ? theme.white : theme.black,
        onClick: () => {
          setPermission(record.pk, UserRole.STAFF);
        },
        hidden: !user?.is_staff || record.is_staff
      },
      {
        title: t`Make superuser`,
        color: theme.colorScheme === 'dark' ? theme.white : theme.black,
        onClick: () => {
          setPermission(record.pk, UserRole.SUPERUSER);
        },
        hidden: !user?.is_superuser || record.is_superuser
      },
      RowEditAction({
        onClick: () => {
          openEditApiForm({
            url: ApiPaths.user_list,
            pk: record.pk,
            title: t`Edit user`,
            fields: {
              email: {},
              first_name: {},
              last_name: {}
            },
            onFormSuccess: refreshTable,
            successMessage: t`User updated`
          });
        }
      }),
      RowDeleteAction({
        onClick: () => {
          openDeleteApiForm({
            url: ApiPaths.user_list,
            pk: record.pk,
            title: t`Delete user`,
            successMessage: t`user deleted`,
            onFormSuccess: refreshTable,
            preFormContent: (
              <Text>{t`Are you sure you want to delete this user?`}</Text>
            )
          });
        }
      })
    ];
  }, []);

  const addUser = useCallback(() => {
    openCreateApiForm({
      url: ApiPaths.user_list,
      title: t`Add user`,
      fields: {
        username: {},
        email: {},
        first_name: {},
        last_name: {}
      },
      onFormSuccess: refreshTable,
      successMessage: t`Added user`
    });
  }, []);

  const tableActions = useMemo(() => {
    let actions = [];

    actions.push(
      <AddItemButton key="add-user" onClick={addUser} tooltip={t`Add user`} />
    );

    return actions;
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.user_list)}
      tableKey={tableKey}
      columns={columns}
      props={{
        rowActions: rowActions,
        customActionGroups: tableActions
      }}
    />
  );
}
