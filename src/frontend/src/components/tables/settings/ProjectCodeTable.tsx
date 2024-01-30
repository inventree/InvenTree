import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { UserRoles } from '../../../enums/Roles';
import { projectCodeFields } from '../../../forms/CommonForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../../hooks/UseForm';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { AddItemButton } from '../../buttons/AddItemButton';
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

  const newProjectCode = useCreateApiFormModal({
    url: ApiPaths.project_code_list,
    title: t`Add Project Code`,
    fields: projectCodeFields(),
    onFormSuccess: table.refreshTable
  });

  const [selectedProjectCode, setSelectedProjectCode] = useState<
    number | undefined
  >(undefined);

  const editProjectCode = useEditApiFormModal({
    url: ApiPaths.project_code_list,
    pk: selectedProjectCode,
    title: t`Edit Project Code`,
    fields: projectCodeFields(),
    onFormSuccess: table.refreshTable
  });

  const deleteProjectCode = useDeleteApiFormModal({
    url: ApiPaths.project_code_list,
    pk: selectedProjectCode,
    title: t`Delete Project Code`,
    onFormSuccess: table.refreshTable
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
    let actions = [];

    actions.push(
      <AddItemButton
        onClick={() => newProjectCode.open()}
        tooltip={t`Add project code`}
      />
    );

    return actions;
  }, []);

  return (
    <>
      {newProjectCode.modal}
      {editProjectCode.modal}
      {deleteProjectCode.modal}
      <InvenTreeTable
        url={apiUrl(ApiPaths.project_code_list)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions
        }}
      />
    </>
  );
}
