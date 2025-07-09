import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableColumn } from '@lib/types/Tables';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import { customUnitsFields } from '../../forms/CommonForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { InvenTreeTable } from '../InvenTreeTable';

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
        switchable: false,
        sortable: true
      },
      {
        accessor: 'definition',
        switchable: false,
        sortable: false
      },
      {
        accessor: 'symbol',
        switchable: false,
        sortable: true
      }
    ];
  }, []);

  const newUnit = useCreateApiFormModal({
    url: ApiEndpoints.custom_unit_list,
    title: t`Add Custom Unit`,
    fields: customUnitsFields(),
    table: table
  });

  const [selectedUnit, setSelectedUnit] = useState<number>(-1);

  const editUnit = useEditApiFormModal({
    url: ApiEndpoints.custom_unit_list,
    pk: selectedUnit,
    title: t`Edit Custom Unit`,
    fields: customUnitsFields(),
    onFormSuccess: (record: any) => table.updateRecord(record)
  });

  const deleteUnit = useDeleteApiFormModal({
    url: ApiEndpoints.custom_unit_list,
    pk: selectedUnit,
    title: t`Delete Custom Unit`,
    table: table
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
    const actions = [];

    actions.push(
      <AddItemButton
        tooltip={t`Add custom unit`}
        onClick={() => newUnit.open()}
        hidden={!user.isStaff() || !user.hasChangeRole(UserRoles.admin)}
      />
    );

    return actions;
  }, [user]);

  return (
    <>
      {newUnit.modal}
      {editUnit.modal}
      {deleteUnit.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.custom_unit_list)}
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
