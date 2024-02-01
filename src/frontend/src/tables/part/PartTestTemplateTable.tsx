import { t } from '@lingui/macro';
import { useCallback, useMemo } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { partTestTemplateFields } from '../../forms/PartForms';
import {
  openCreateApiForm,
  openDeleteApiForm,
  openEditApiForm
} from '../../functions/forms';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { BooleanColumn, DescriptionColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../RowActions';

export default function PartTestTemplateTable({ partId }: { partId: number }) {
  const table = useTable('part-test-template');
  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'test_name',
        title: t`Test Name`,
        switchable: false,
        sortable: true
      },
      DescriptionColumn({
        switchable: false
      }),
      BooleanColumn({
        accessor: 'required',
        title: t`Required`
      }),
      BooleanColumn({
        accessor: 'requires_value',
        title: t`Requires Value`
      }),
      BooleanColumn({
        accessor: 'requires_attachment',
        title: t`Requires Attachment`
      })
    ];
  }, []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'required',
        label: t`Required`,
        description: t`Show required tests`
      },
      {
        name: 'requires_value',
        label: t`Requires Value`,
        description: t`Show tests that require a value`
      },
      {
        name: 'requires_attachment',
        label: t`Requires Attachment`,
        description: t`Show tests that require an attachment`
      }
    ];
  }, []);

  const rowActions = useCallback(
    (record: any) => {
      let can_edit = user.hasChangeRole(UserRoles.part);
      let can_delete = user.hasDeleteRole(UserRoles.part);

      return [
        RowEditAction({
          hidden: !can_edit,
          onClick: () => {
            openEditApiForm({
              url: ApiEndpoints.part_test_template_list,
              pk: record.pk,
              title: t`Edit Test Template`,
              fields: partTestTemplateFields(),
              successMessage: t`Template updated`,
              onFormSuccess: table.refreshTable
            });
          }
        }),
        RowDeleteAction({
          hidden: !can_delete,
          onClick: () => {
            openDeleteApiForm({
              url: ApiEndpoints.part_test_template_list,
              pk: record.pk,
              title: t`Delete Test Template`,
              successMessage: t`Test Template deleted`,
              onFormSuccess: table.refreshTable
            });
          }
        })
      ];
    },
    [user]
  );

  const addTestTemplate = useCallback(() => {
    let fields = partTestTemplateFields();

    fields['part'].value = partId;

    openCreateApiForm({
      url: ApiEndpoints.part_test_template_list,
      title: t`Create Test Template`,
      fields: fields,
      successMessage: t`Template created`,
      onFormSuccess: table.refreshTable
    });
  }, [partId]);

  const tableActions = useMemo(() => {
    let can_add = user.hasAddRole(UserRoles.part);

    return [
      <AddItemButton
        tooltip={t`Add Test Template`}
        onClick={addTestTemplate}
        disabled={!can_add}
      />
    ];
  }, [user]);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.part_test_template_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          part: partId
        },
        tableFilters: tableFilters,
        tableActions: tableActions,
        rowActions: rowActions
      }}
    />
  );
}
