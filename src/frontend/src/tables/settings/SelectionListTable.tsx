import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { DetailDrawer } from '@lib/components/nav/DetailDrawer';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { TableColumn } from '@lib/types/Tables';
import {
  BooleanColumn,
  DescriptionColumn
} from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { selectionListFields } from '../../forms/CommonForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';
import SelectionListDrawer from './SelectionListDrawer';

/**
 * Table for displaying list of selectionlist items
 */
export default function SelectionListTable() {
  const table = useTable('selectionlist');
  const navigate = useNavigate();

  const user = useUserState();

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        sortable: true
      },
      DescriptionColumn({
        sortable: true
      }),
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
            navigate(`${record.pk}/`);
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
      {deleteSelectionList.modal}
      <DetailDrawer
        title={t`Selection List`}
        size='xl'
        renderContent={(id) =>
          id ? (
            <SelectionListDrawer id={id} refreshTable={table.refreshTable} />
          ) : null
        }
      />
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.selectionlist_list)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions,
          enableDownload: true,
          onRowClick: (record) => {
            navigate(`${record.pk}/`);
          }
        }}
      />
    </>
  );
}
