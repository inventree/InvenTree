import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import { projectCodeFields } from '../../forms/CommonForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import { DescriptionColumn, ResponsibleColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

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
          enableDownload: true
        }}
      />
    </>
  );
}
