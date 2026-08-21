import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { RowDeleteAction, RowEditAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { RowAction } from '@lib/types/Tables';
import {
  DecimalColumn,
  NoteColumn,
  PartColumn,
  StockColumn
} from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { useNonConformanceStockItemFields } from '../../forms/NCRForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';

export default function NonConformanceStockItemTable({
  ncrId,
  partId
}: Readonly<{
  ncrId?: number;
  partId?: number;
}>) {
  const user = useUserState();
  const table = useTable('ncr-stock-item');

  const tableColumns = useMemo(() => {
    return [
      PartColumn({
        accessor: 'stock_item_detail.part_detail'
      }),
      StockColumn({
        accessor: 'stock_item_detail'
      }),
      DecimalColumn({
        accessor: 'quantity'
      }),
      NoteColumn({})
    ];
  }, []);

  const [selectedItemId, setSelectedItemId] = useState<number>(0);

  const addFields = useNonConformanceStockItemFields({ ncrId, partId });
  const editFields = useNonConformanceStockItemFields({ ncrId, partId });

  const addStockItem = useCreateApiFormModal({
    url: ApiEndpoints.ncr_stock_item_list,
    title: t`Link Stock Item`,
    fields: addFields,
    table: table
  });

  const editItem = useEditApiFormModal({
    pk: selectedItemId,
    url: ApiEndpoints.ncr_stock_item_list,
    title: t`Edit Linked Stock Item`,
    fields: editFields,
    table: table
  });

  const deleteItem = useDeleteApiFormModal({
    pk: selectedItemId,
    url: ApiEndpoints.ncr_stock_item_list,
    title: t`Unlink Stock Item`,
    table: table
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.ncr),
          onClick: () => {
            setSelectedItemId(record.pk);
            editItem.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.ncr),
          tooltip: t`Unlink stock item`,
          onClick: () => {
            setSelectedItemId(record.pk);
            deleteItem.open();
          }
        })
      ];
    },
    [user]
  );

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-ncr-stock-item'
        tooltip={t`Link Stock Item`}
        onClick={() => addStockItem.open()}
        hidden={!user.hasAddRole(UserRoles.ncr) || !ncrId}
      />
    ];
  }, [user, ncrId]);

  return (
    <>
      {addStockItem.modal}
      {editItem.modal}
      {deleteItem.modal}
      <InvenTreeTable
        tableState={table}
        url={apiUrl(ApiEndpoints.ncr_stock_item_list)}
        columns={tableColumns}
        props={{
          params: {
            ncr: ncrId,
            stock_item_detail: true
          },
          rowActions: rowActions,
          tableActions: tableActions,
          modelType: ModelType.stockitem,
          modelField: 'stock_item'
        }}
      />
    </>
  );
}
