import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { customStateFields } from '../../forms/CommonForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

/**
 * Table for displaying list of custom states
 */
export default function CustomStateTable() {
  const table = useTable('customstates');

  const user = useUserState();

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        sortable: true
      },
      {
        accessor: 'label',
        title: t`Display Name`,
        sortable: true
      },
      {
        accessor: 'color'
      },
      {
        accessor: 'key',
        sortable: true
      },
      {
        accessor: 'logical_key',
        sortable: true
      },
      {
        accessor: 'model_name',
        title: t`Model`,
        sortable: true
      },
      {
        accessor: 'reference_status',
        title: t`Status`,
        sortable: true
      }
    ];
  }, []);

  const newCustomState = useCreateApiFormModal({
    url: ApiEndpoints.custom_state_list,
    title: t`Add State`,
    fields: customStateFields(),
    table: table
  });

  const [selectedCustomState, setSelectedCustomState] = useState<
    number | undefined
  >(undefined);

  const editCustomState = useEditApiFormModal({
    url: ApiEndpoints.custom_state_list,
    pk: selectedCustomState,
    title: t`Edit State`,
    fields: customStateFields(),
    table: table
  });

  const deleteCustomState = useDeleteApiFormModal({
    url: ApiEndpoints.custom_state_list,
    pk: selectedCustomState,
    title: t`Delete State`,
    table: table
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.admin),
          onClick: () => {
            setSelectedCustomState(record.pk);
            editCustomState.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.admin),
          onClick: () => {
            setSelectedCustomState(record.pk);
            deleteCustomState.open();
          }
        })
      ];
    },
    [user]
  );

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        onClick={() => newCustomState.open()}
        tooltip={t`Add state`}
      />
    ];
  }, []);

  return (
    <>
      {newCustomState.modal}
      {editCustomState.modal}
      {deleteCustomState.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.custom_state_list)}
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
