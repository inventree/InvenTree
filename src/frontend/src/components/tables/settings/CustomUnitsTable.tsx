import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { UserRoles } from '../../../enums/Roles';
import { customUnitsFields } from '../../../forms/CommonForms';
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
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

/**
 * Table for displaying list of custom physical units
 */
export default function CustomUnitsTable() {
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

  const newUnit = useCreateApiFormModal({
    url: ApiPaths.custom_unit_list,
    title: t`Add Custom Unit`,
    fields: customUnitsFields(),
    onFormSuccess: table.refreshTable
  });

  const [selectedUnit, setSelectedUnit] = useState<number | undefined>(
    undefined
  );

  const editUnit = useEditApiFormModal({
    url: ApiPaths.custom_unit_list,
    pk: selectedUnit,
    title: t`Edit Custom Unit`,
    fields: customUnitsFields(),
    onFormSuccess: table.refreshTable
  });

  const deleteUnit = useDeleteApiFormModal({
    url: ApiPaths.custom_unit_list,
    pk: selectedUnit,
    title: t`Delete Custom Unit`,
    onFormSuccess: table.refreshTable
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.admin),
          onClick: () => {
            setSelectedUnit(record.pk);
            editUnit.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.admin),
          onClick: () => {
            setSelectedUnit(record.pk);
            deleteUnit.open();
          }
        })
      ];
    },
    [user]
  );

  const tableActions = useMemo(() => {
    let actions = [];

    actions.push(
      // TODO: Adjust actions based on user permissions
      <AddItemButton
        tooltip={t`Add custom unit`}
        onClick={() => newUnit.open()}
      />
    );

    return actions;
  }, []);

  return (
    <>
      {newUnit.modal}
      {editUnit.modal}
      {deleteUnit.modal}
      <InvenTreeTable
        url={apiUrl(ApiPaths.custom_unit_list)}
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
