import { type RowAction, RowEditAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { StockOperationProps } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { Alert } from '@mantine/core';
import { IconCircleX } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { useTransferOrderAllocationFields } from '../../forms/TransferOrderForms';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useStockAdjustActions } from '../../hooks/UseStockAdjustActions';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  DescriptionColumn,
  LocationColumn,
  PartColumn,
  ReferenceColumn,
  StatusColumn
} from '../ColumnRenderers';
import { IncludeVariantsFilter, StockLocationFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export default function TransferOrderAllocationTable({
  partId,
  stockId,
  orderId,
  lineItemId,
  showPartInfo,
  showOrderInfo,
  allowEdit,
  isSubTable,
  modelTarget,
  modelField
}: Readonly<{
  partId?: number;
  stockId?: number;
  orderId?: number;
  lineItemId?: number;
  showPartInfo?: boolean;
  showOrderInfo?: boolean;
  allowEdit?: boolean;
  isSubTable?: boolean;
  modelTarget?: ModelType;
  modelField?: string;
}>) {
  const user = useUserState();

  const tableId = useMemo(() => {
    let id = 'transferorderallocations';

    if (!!partId) {
      id += '-part';
    }

    if (isSubTable) {
      id += '-sub';
    }

    return id;
  }, [partId, isSubTable]);

  const table = useTable(tableId);

  const [selectedAllocation, setSelectedAllocation] = useState<number>(0);

  const tableFilters: TableFilter[] = useMemo(() => {
    const filters: TableFilter[] = [
      {
        name: 'outstanding',
        label: t`Outstanding`,
        description: t`Show outstanding allocations`
      },
      StockLocationFilter()
    ];

    if (!!partId) {
      filters.push(IncludeVariantsFilter());
    }

    return filters;
  }, [partId]);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      ReferenceColumn({
        accessor: 'order_detail.reference',
        title: t`Transfer Order`,
        switchable: false,
        sortable: true,
        hidden: showOrderInfo != true
      }),
      DescriptionColumn({
        accessor: 'order_detail.description',
        hidden: showOrderInfo != true
      }),
      StatusColumn({
        accessor: 'order_detail.status',
        model: ModelType.transferorder,
        title: t`Order Status`,
        hidden: showOrderInfo != true
      }),
      PartColumn({
        hidden: showPartInfo != true,
        part: 'part_detail'
      }),
      DescriptionColumn({
        accessor: 'part_detail.description',
        hidden: showPartInfo != true
      }),
      {
        accessor: 'part_detail.IPN',
        title: t`IPN`,
        hidden: showPartInfo != true,
        sortable: true,
        ordering: 'IPN'
      },
      {
        accessor: 'serial',
        title: t`Serial Number`,
        sortable: true,
        switchable: true,
        render: (record: any) => record?.item_detail?.serial
      },
      {
        accessor: 'batch',
        title: t`Batch Code`,
        sortable: true,
        switchable: true,
        render: (record: any) => record?.item_detail?.batch
      },
      {
        accessor: 'available',
        title: t`Available Quantity`,
        sortable: false,
        hidden: isSubTable,
        render: (record: any) => record?.item_detail?.quantity
      },
      {
        accessor: 'quantity',
        title: t`Allocated Quantity`,
        sortable: true
      },
      LocationColumn({
        accessor: 'location_detail',
        switchable: true,
        sortable: true
      })
    ];
  }, [showOrderInfo, showPartInfo, isSubTable]);

  const editAllocationFields = useTransferOrderAllocationFields({
    orderId: orderId
  });

  const editAllocation = useEditApiFormModal({
    url: ApiEndpoints.transfer_order_allocation_list,
    pk: selectedAllocation,
    fields: editAllocationFields,
    title: t`Edit Allocation`,
    onFormSuccess: () => table.refreshTable()
  });

  const deleteAllocation = useDeleteApiFormModal({
    url: ApiEndpoints.transfer_order_allocation_list,
    pk: selectedAllocation,
    title: t`Remove Allocated Stock`,
    preFormContent: (
      <Alert color='red' title={t`Confirm Removal`}>
        {t`Are you sure you want to remove this allocated stock from the order?`}
      </Alert>
    ),
    submitText: t`Remove`,
    onFormSuccess: () => table.refreshTable()
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          tooltip: t`Edit Allocation`,
          hidden: !allowEdit || !user.hasChangeRole(UserRoles.transfer_order),
          onClick: () => {
            setSelectedAllocation(record.pk);
            editAllocation.open();
          }
        }),
        {
          title: t`Remove`,
          tooltip: t`Remove allocated stock`,
          icon: <IconCircleX />,
          color: 'red',
          hidden: !allowEdit || !user.hasDeleteRole(UserRoles.transfer_order),
          onClick: () => {
            setSelectedAllocation(record.pk);
            deleteAllocation.open();
          }
        }
      ];
    },
    [allowEdit, user]
  );

  const stockOperationProps: StockOperationProps = useMemo(() => {
    // Extract stock items from the selected records
    // Note that the table is actually a list of TransferOrderAllocation instances,
    // so we need to reconstruct the stock item details
    const stockItems: any[] = table.selectedRecords
      .filter((item: any) => !!item.item_detail)
      .map((item: any) => {
        return {
          ...item.item_detail,
          part_detail: item.part_detail,
          location_detail: item.location_detail
        };
      });

    return {
      items: stockItems,
      model: ModelType.stockitem,
      refresh: table.refreshTable
    };
  }, [table.selectedRecords, table.refreshTable]);

  const stockAdjustActions = useStockAdjustActions({
    formProps: stockOperationProps,
    merge: false,
    assign: false,
    delete: false,
    add: false,
    count: false,
    remove: false
  });

  const tableActions = useMemo(() => {
    return [stockAdjustActions.dropdown];
  }, [allowEdit, orderId, user, stockAdjustActions.dropdown]);

  return (
    <>
      {editAllocation.modal}
      {deleteAllocation.modal}
      {!isSubTable && stockAdjustActions.modals.map((modal) => modal.modal)}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.transfer_order_allocation_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            part_detail: showPartInfo ?? false,
            order_detail: showOrderInfo ?? false,
            item_detail: true,
            location_detail: true,
            line: lineItemId,
            part: partId,
            order: orderId,
            item: stockId
          },
          enableSearch: !isSubTable,
          enableRefresh: !isSubTable,
          enableColumnSwitching: !isSubTable,
          enableFilters: !isSubTable,
          enableDownload: !isSubTable,
          enableSelection: !isSubTable,
          minHeight: isSubTable ? 100 : undefined,
          rowActions: rowActions,
          tableActions: isSubTable ? undefined : tableActions,
          tableFilters: tableFilters,
          modelField: modelField ?? 'order',
          enableReports: !isSubTable,
          enableLabels: !isSubTable,
          printingAccessor: 'item',
          modelType: modelTarget ?? ModelType.transferorder
        }}
      />
    </>
  );
}
