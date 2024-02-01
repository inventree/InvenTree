import { t } from '@lingui/macro';
import { useCallback, useMemo } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import {
  openCreateApiForm,
  openDeleteApiForm,
  openEditApiForm
} from '../../functions/forms';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { DescriptionColumn, ResponsibleColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

/**
 * Table for displaying list of project codes
 */
export default function ProjectCodeTable() {
  const table = useTable('project-codes');

  const user = useUserState();

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'code',
        sortable: true,
        title: t`Project Code`
      },
      DescriptionColumn({}),
      ResponsibleColumn()
    ];
  }, []);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.admin),
          onClick: () => {
            openEditApiForm({
              url: ApiEndpoints.project_code_list,
              pk: record.pk,
              title: t`Edit project code`,
              fields: {
                code: {},
                description: {},
                responsible: {}
              },
              onFormSuccess: table.refreshTable,
              successMessage: t`Project code updated`
            });
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.admin),
          onClick: () => {
            openDeleteApiForm({
              url: ApiEndpoints.project_code_list,
              pk: record.pk,
              title: t`Delete project code`,
              successMessage: t`Project code deleted`,
              onFormSuccess: table.refreshTable,
              preFormWarning: t`Are you sure you want to remove this project code?`
            });
          }
        })
      ];
    },
    [user]
  );

  const addProjectCode = useCallback(() => {
    openCreateApiForm({
      url: ApiEndpoints.project_code_list,
      title: t`Add project code`,
      fields: {
        code: {},
        description: {},
        responsible: {}
      },
      onFormSuccess: table.refreshTable,
      successMessage: t`Added project code`
    });
  }, []);

  const tableActions = useMemo(() => {
    let actions = [];

    actions.push(
      <AddItemButton onClick={addProjectCode} tooltip={t`Add project code`} />
    );

    return actions;
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.project_code_list)}
      tableState={table}
      columns={columns}
      props={{
        rowActions: rowActions,
        tableActions: tableActions
      }}
    />
  );
}
