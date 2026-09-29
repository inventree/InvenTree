import { t } from '@lingui/core/macro';
import { Center } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

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
import type { TableColumn } from '@lib/types/Tables';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import {
  DateColumn,
  NoteColumn
} from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { formatCurrency } from '../../defaults/formatters';
import {
  StockItemCostEntryFormAlert,
  useStockItemCostEntryFields
} from '../../forms/PricingForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';

export default function StockItemCostEntryTable({
  itemId
}: Readonly<{
  itemId: number;
}>) {
  const user = useUserState();
  const table = useTable('stockitemcostentry');

  const fields = useStockItemCostEntryFields();

  const tableUrl = useMemo(
    () => apiUrl(ApiEndpoints.stock_item_cost_entry_list),
    []
  );

  const newCostEntry = useCreateApiFormModal({
    url: tableUrl,
    title: t`Add Cost Entry`,
    fields: fields,
    preFormContent: <StockItemCostEntryFormAlert />,
    initialData: {
      stock_item: itemId
    },
    onFormSuccess: (data: any) => {
      table.updateRecord(data);
    }
  });

  const [selectedCostEntry, setSelectedCostEntry] = useState<number>(0);

  const editCostEntry = useEditApiFormModal({
    url: tableUrl,
    pk: selectedCostEntry,
    title: t`Edit Cost Entry`,
    fields: fields,
    preFormContent: <StockItemCostEntryFormAlert />,
    onFormSuccess: (data: any) => {
      table.updateRecord(data);
    }
  });

  const deleteCostEntry = useDeleteApiFormModal({
    url: tableUrl,
    pk: selectedCostEntry,
    title: t`Delete Cost Entry`,
    table: table
  });

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'cost_type',
        title: t`Cost Type`,
        sortable: true,
        switchable: false,
        render: (record: any) => (
          <Center>
            <StatusRenderer status={record.cost_type} type='CostType' />
          </Center>
        )
      },
      {
        accessor: 'min_cost',
        title: t`Minimum Cost`,
        sortable: true,
        render: (record: any) =>
          formatCurrency(record.min_cost, {
            currency: record.min_cost_currency
          })
      },
      {
        accessor: 'max_cost',
        title: t`Maximum Cost`,
        sortable: true,
        render: (record: any) =>
          formatCurrency(record.max_cost, {
            currency: record.max_cost_currency
          })
      },
      DateColumn({}),
      NoteColumn({})
    ];
  }, []);

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-cost-entry'
        tooltip={t`Add Cost Entry`}
        onClick={() => {
          newCostEntry.open();
        }}
        hidden={!user.hasAddRole(UserRoles.pricing)}
      />
    ];
  }, [user]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.pricing),
          onClick: () => {
            setSelectedCostEntry(record.pk);
            editCostEntry.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.pricing),
          onClick: () => {
            setSelectedCostEntry(record.pk);
            deleteCostEntry.open();
          }
        })
      ];
    },
    [user]
  );

  return (
    <>
      {newCostEntry.modal}
      {editCostEntry.modal}
      {deleteCostEntry.modal}
      <InvenTreeTable
        tableState={table}
        url={tableUrl}
        columns={columns}
        props={{
          params: {
            stock_item: itemId
          },
          tableActions: tableActions,
          rowActions: rowActions,
          enableDownload: true
        }}
      />
    </>
  );
}
