import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useCallback, useMemo, useState } from 'react';

import {
  openCreateApiForm,
  openDeleteApiForm,
  openEditApiForm
} from '../../../functions/forms';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { AddItemButton } from '../../buttons/AddItemButton';
import { TableColumn } from '../Column';
import { BooleanColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction, RowEditAction } from '../RowActions';
import { UserDrawer } from './UserDrawer';

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
  const [opened, { open, close }] = useDisclosure(false);
  const [userDetail, setUserDetail] = useState<{}>();

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
      {
        accessor: 'groups',
        sortable: true,
        switchable: true,
        title: t`Groups`,
        render: (record: any) => {
          return record.groups.length;
        }
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
    return [
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
    <>
      <UserDrawer opened={opened} close={close} userDetail={userDetail} />
      <InvenTreeTable
        url={apiUrl(ApiPaths.user_list)}
        tableKey={tableKey}
        columns={columns}
        props={{
          rowActions: rowActions,
          customActionGroups: tableActions,
          onRowClick: (record: any) => {
            console.log(record);
            setUserDetail(record);
            open();
          }
        }}
      />
    </>
  );
}
