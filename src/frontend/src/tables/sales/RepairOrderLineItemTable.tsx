import { ActionButton } from '@lib/components/ActionButton';
import { AddItemButton } from '@lib/components/AddItemButton';
import { ProgressBar } from '@lib/components/ProgressBar';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { IconArrowRight, IconWand } from '@tabler/icons-react';
import type { DataTableRowExpansionProps } from 'mantine-datatable';
import { useCallback, useMemo, useState } from 'react';
import { RenderStockItem } from '../../components/render/Stock';
import {
  DescriptionColumn,
  PartColumn
} from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import {
  useAllocateStockToRepairOrderForm,
  useRepairOrderAutoAllocateFields,
  useRepairOrderLineItemFields
} from '../../forms/RepairOrderForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';

function RepairOrderLineAllocationTable({
  lineItem,
  editable,
  onDeleteAllocation
}: Readonly<{
  lineItem: any;
  editable: boolean;
  onDeleteAllocation: (pk: number) => void;
}>) {
  const table = useTable(`repair-order-line-allocations-${lineItem.pk}`);
  const user = useUserState();

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'item',
        title: t`Stock Item`,
        render: (record: any) =>
          record.item_detail ? (
            <RenderStockItem instance={record.item_detail} />
          ) : null
      },
      {
        accessor: 'quantity',
        title: t`Allocated Quantity`,
        sortable: true
      }
    ];
  }, []);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowDeleteAction({
          hidden: !editable || !user.hasDeleteRole(UserRoles.repair_order),
          onClick: () => onDeleteAllocation(record.pk)
        })
      ];
    },
    [editable, user]
  );

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.repair_order_allocation_list)}
      tableState={table}
      columns={columns}
      props={{
        params: {
          line: lineItem.pk,
          item_detail: true
        },
        rowActions: rowActions,
        modelType: ModelType.repairorderallocation
      }}
    />
  );
}

export default function RepairOrderLineItemTable({
  orderId,
  assemblyPartId,
  orderDetailRefresh,
  editable
}: Readonly<{
  orderId: number;
  assemblyPartId?: number;
  orderDetailRefresh: () => void;
  editable: boolean;
}>) {
  const table = useTable('repair-order-line-item');
  const user = useUserState();

  const [selectedLine, setSelectedLine] = useState<number>(0);
  const [selectedLineItem, setSelectedLineItem] = useState<any>({});

  const newLineFields = useRepairOrderLineItemFields({
    orderId: orderId,
    assemblyPartId: assemblyPartId,
    create: true
  });

  const editLineFields = useRepairOrderLineItemFields({
    orderId: orderId,
    assemblyPartId: assemblyPartId
  });

  const newLine = useCreateApiFormModal({
    url: ApiEndpoints.repair_order_line_list,
    title: t`Add Line Item`,
    fields: newLineFields,
    initialData: {
      order: orderId
    },
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const editLine = useEditApiFormModal({
    url: ApiEndpoints.repair_order_line_list,
    pk: selectedLine,
    title: t`Edit Line Item`,
    fields: editLineFields,
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const deleteLine = useDeleteApiFormModal({
    url: ApiEndpoints.repair_order_line_list,
    pk: selectedLine,
    title: t`Delete Line Item`,
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const allocateStock = useAllocateStockToRepairOrderForm({
    lineItem: selectedLineItem,
    onFormSuccess: () => table.refreshTable()
  });

  const [selectedAllocation, setSelectedAllocation] = useState<number>(0);

  const deleteAllocation = useDeleteApiFormModal({
    url: ApiEndpoints.repair_order_allocation_list,
    pk: selectedAllocation,
    title: t`Delete Allocation`,
    onFormSuccess: () => table.refreshTable()
  });

  const autoAllocateFields = useRepairOrderAutoAllocateFields();

  const autoAllocateStock = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.repair_order_auto_allocate, orderId),
    title: t`Auto Allocate Stock`,
    fields: autoAllocateFields,
    preFormWarning: t`Automatically allocate available stock against outstanding line items`,
    successMessage: t`Stock allocated`,
    onFormSuccess: () => table.refreshTable()
  });

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({
        part: 'part_detail',
        ordering: 'part'
      }),
      DescriptionColumn({
        accessor: 'part_detail.description'
      }),
      {
        accessor: 'quantity',
        title: t`Quantity`,
        sortable: true
      },
      {
        accessor: 'allocated',
        title: t`Allocated`,
        sortable: true,
        minWidth: 125,
        render: (record: any) => (
          <ProgressBar
            progressLabel
            value={record.allocated}
            maximum={record.quantity}
          />
        )
      }
    ];
  }, []);

  const tableActions = useMemo(() => {
    const canAllocate = editable && user.hasAddRole(UserRoles.repair_order);

    return [
      <ActionButton
        key='auto-allocate'
        icon={<IconWand />}
        tooltip={t`Auto Allocate Stock`}
        hidden={!canAllocate}
        color='blue'
        onClick={() => autoAllocateStock.open()}
      />,
      <AddItemButton
        key='add-line-item'
        tooltip={t`Add Line Item`}
        hidden={!editable || !user.hasAddRole(UserRoles.repair_order)}
        onClick={() => {
          newLine.open();
        }}
      />
    ];
  }, [user, editable]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const canAllocate =
        editable &&
        !!record.part &&
        record.allocated < record.quantity &&
        user.hasAddRole(UserRoles.repair_order);

      return [
        {
          icon: <IconArrowRight />,
          title: t`Allocate Stock`,
          hidden: !canAllocate,
          color: 'green',
          onClick: () => {
            setSelectedLineItem(record);
            allocateStock.open();
          }
        },
        RowEditAction({
          hidden: !editable || !user.hasChangeRole(UserRoles.repair_order),
          onClick: () => {
            setSelectedLine(record.pk);
            editLine.open();
          }
        }),
        RowDeleteAction({
          hidden: !editable || !user.hasDeleteRole(UserRoles.repair_order),
          onClick: () => {
            setSelectedLine(record.pk);
            deleteLine.open();
          }
        })
      ];
    },
    [user, editable]
  );

  const rowExpansion: DataTableRowExpansionProps<any> = useMemo(() => {
    return {
      allowMultiple: true,
      expandable: ({ record }: { record: any }) => {
        return table.isRowExpanded(record.pk) || record.allocated > 0;
      },
      content: ({ record }: { record: any }) => (
        <RepairOrderLineAllocationTable
          lineItem={record}
          editable={editable}
          onDeleteAllocation={(pk: number) => {
            setSelectedAllocation(pk);
            deleteAllocation.open();
          }}
        />
      )
    };
  }, [table.isRowExpanded, editable]);

  return (
    <>
      {newLine.modal}
      {editLine.modal}
      {deleteLine.modal}
      {allocateStock.modal}
      {deleteAllocation.modal}
      {autoAllocateStock.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.repair_order_line_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            order: orderId,
            part_detail: true
          },
          tableActions: tableActions,
          rowActions: rowActions,
          rowExpansion: rowExpansion,
          modelType: ModelType.repairorderlineitem
        }}
      />
    </>
  );
}
