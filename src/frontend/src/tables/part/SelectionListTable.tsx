import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { selectionListFields } from '../../forms/selectionListFields';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import { BooleanColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

/**
 * Table for displaying list of selectionlist items
 */
export default function SelectionListTable() {
  const table = useTable('selectionlist');

  const user = useUserState();

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        sortable: true
      },
      {
        accessor: 'description',
        sortable: true
      },
      BooleanColumn({
        accessor: 'active'
      }),
      BooleanColumn({
        accessor: 'locked'
      }),
      {
        accessor: 'source_plugin',
        sortable: true
      },
      {
        accessor: 'source_string',
        sortable: true
      },
      {
        accessor: 'entry_count'
      }
    ];
  }, []);

  const newSelectionList = useCreateApiFormModal({
    url: ApiEndpoints.selectionlist_list,
    title: t`Add Selection List`,
    fields: selectionListFields(),
    table: table
  });

  const [selectedSelectionList, setSelectedSelectionList] = useState<
    number | undefined
  >(undefined);

  const editSelectionList = useEditApiFormModal({
    url: ApiEndpoints.selectionlist_list,
    pk: selectedSelectionList,
    title: t`Edit Selection List`,
    fields: selectionListFields(),
    table: table
  });

  const deleteSelectionList = useDeleteApiFormModal({
    url: ApiEndpoints.selectionlist_list,
    pk: selectedSelectionList,
    title: t`Delete Selection List`,
    table: table
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.admin),
          onClick: () => {
            setSelectedSelectionList(record.pk);
            editSelectionList.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.admin),
          onClick: () => {
            setSelectedSelectionList(record.pk);
            deleteSelectionList.open();
          }
        })
      ];
    },
    [user]
  );

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-selection-list'
        onClick={() => newSelectionList.open()}
        tooltip={t`Add Selection List`}
      />
    ];
  }, []);

  return (
    <>
      {newSelectionList.modal}
      {editSelectionList.modal}
      {deleteSelectionList.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.selectionlist_list)}
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
