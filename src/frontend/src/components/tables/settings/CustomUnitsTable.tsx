import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { useCallback, useMemo } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { UserRoles } from '../../../enums/Roles';
import {
  openCreateApiForm,
  openDeleteApiForm,
  openEditApiForm
} from '../../../functions/forms';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { AddItemButton } from '../../buttons/AddItemButton';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

/**
 * Table for displaying list of custom physical units
 */
export function CustomUnitsTable() {
  const table = useTable('custom-units');

  const user = useUserState();

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Name`,
        switchable: false,
        sortable: true
      },
      {
        accessor: 'definition',
        title: t`Definition`,
        switchable: false,
        sortable: false
      },
      {
        accessor: 'symbol',
        title: t`Symbol`,
        switchable: false,
        sortable: true
      }
    ];
  }, []);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.admin),
          onClick: () => {
            openEditApiForm({
              url: ApiPaths.custom_unit_list,
              pk: record.pk,
              title: t`Edit custom unit`,
              fields: {
                name: {},
                definition: {},
                symbol: {}
              },
              onFormSuccess: table.refreshTable,
              successMessage: t`Custom unit updated`
            });
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.admin),
          onClick: () => {
            openDeleteApiForm({
              url: ApiPaths.custom_unit_list,
              pk: record.pk,
              title: t`Delete custom unit`,
              successMessage: t`Custom unit deleted`,
              onFormSuccess: table.refreshTable,
              preFormContent: (
                <Text>{t`Are you sure you want to remove this custom unit?`}</Text>
              )
            });
          }
        })
      ];
    },
    [user]
  );

  const addCustomUnit = useCallback(() => {
    openCreateApiForm({
      url: ApiPaths.custom_unit_list,
      title: t`Add custom unit`,
      fields: {
        name: {},
        definition: {},
        symbol: {}
      },
      successMessage: t`Custom unit created`,
      onFormSuccess: table.refreshTable
    });
  }, []);

  const tableActions = useMemo(() => {
    let actions = [];

    actions.push(
      // TODO: Adjust actions based on user permissions
      <AddItemButton tooltip={t`Add custom unit`} onClick={addCustomUnit} />
    );

    return actions;
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.custom_unit_list)}
      tableState={table}
      columns={columns}
      props={{
        rowActions: rowActions,
        customActionGroups: tableActions
      }}
    />
  );
}
