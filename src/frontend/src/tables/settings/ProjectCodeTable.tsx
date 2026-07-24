import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { TableFilter } from '@lib/index';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';
import {
  BooleanColumn,
  DescriptionColumn,
  ResponsibleColumn
} from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { projectCodeFields } from '../../forms/CommonForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';

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
        sortable: true
      },
      DescriptionColumn({}),
      BooleanColumn({
        accessor: 'active'
      }),
      ResponsibleColumn({})
    ];
  }, []);

  const newProjectCode = useCreateApiFormModal({
    url: ApiEndpoints.project_code_list,
    title: t`Add Project Code`,
    fields: projectCodeFields(),
    table: table
  });

  const [selectedProjectCode, setSelectedProjectCode] = useState<
    number | undefined
  >(undefined);

  const editProjectCode = useEditApiFormModal({
    url: ApiEndpoints.project_code_list,
    pk: selectedProjectCode,
    title: t`Edit Project Code`,
    fields: projectCodeFields(),
    table: table
  });

  const deleteProjectCode = useDeleteApiFormModal({
    url: ApiEndpoints.project_code_list,
    pk: selectedProjectCode,
    title: t`Delete Project Code`,
    table: table
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.admin),
          onClick: () => {
            setSelectedProjectCode(record.pk);
            editProjectCode.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.admin),
          onClick: () => {
            setSelectedProjectCode(record.pk);
            deleteProjectCode.open();
          }
        })
      ];
    },
    [user]
  );

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'active',
        label: t`Active`,
        description: t`Show active items`,
        type: 'boolean'
      }
    ];
  }, []);

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add'
        onClick={() => newProjectCode.open()}
        tooltip={t`Add project code`}
      />
    ];
  }, []);

  return (
    <>
      {newProjectCode.modal}
      {editProjectCode.modal}
      {deleteProjectCode.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.project_code_list)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions,
          tableFilters: tableFilters,
          enableDownload: true
        }}
      />
    </>
  );
}
