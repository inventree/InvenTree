import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import { ActionButton } from '@lib/components/ActionButton';
import {
  type RowAction,
  RowEditAction,
  RowViewAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { StockOperationProps } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { Alert } from '@mantine/core';
import { IconCircleX, IconTruckDelivery } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { formatDate } from '../../defaults/formatters';
import { useSalesOrderAllocationFields } from '../../forms/SalesOrderForms';
import {
  useBulkEditApiFormModal,
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

export default function SalesOrderAllocationTable({
  partId,
  stockId,
  orderId,
  lineItemId,
  shipmentId,
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
  shipmentId?: number;
  showPartInfo?: boolean;
  showOrderInfo?: boolean;
  allowEdit?: boolean;
  isSubTable?: boolean;
  modelTarget?: ModelType;
  modelField?: string;
}>) {
  const user = useUserState();
  const navigate = useNavigate();

  const tableId = useMemo(() => {
    let id = 'salesorderallocations';

    if (!!partId) {
      id += '-part';
    }

    if (isSubTable) {
      id += '-sub';
    }

    return id;
  }, [partId, isSubTable]);

  const table = useTable(tableId);

  const tableFilters: TableFilter[] = useMemo(() => {
    const filters: TableFilter[] = [
      {
        name: 'outstanding',
        label: t`Outstanding`,
        description: t`Show outstanding allocations`
      },
      {
        name: 'assigned_to_shipment',
        label: t`Assigned to Shipment`,
        description: t`Show allocations assigned to a shipment`
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
        title: t`Sales Order`,
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
        model: ModelType.salesorder,
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
      }),
      {
        accessor: 'shipment_detail.reference',
        title: t`Shipment`,
        switchable: true,
        sortable: false,
        render: (record: any) => {
          return record.shipment_detail?.reference ?? t`No shipment`;
        }
      },
      {
        accessor: 'shipment_date',
        title: t`Shipment Date`,
        switchable: true,
        sortable: true,
        render: (record: any) => {
          if (record.shipment_detail?.shipment_date) {
            return formatDate(record.shipment_detail.shipment_date);
          } else if (record.shipment) {
            return t`Not shipped`;
          } else {
            return t`No shipment`;
          }
        }
      }
    ];
  }, [showOrderInfo, showPartInfo, isSubTable]);

  const [selectedAllocation, setSelectedAllocation] = useState<number>(0);

  const [selectedShipment, setSelectedShipment] = useState<any | null>(null);

  const editAllocationFields = useSalesOrderAllocationFields({
    orderId: orderId,
    shipment: selectedShipment
  });

  const editAllocation = useEditApiFormModal({
    url: ApiEndpoints.sales_order_allocation_list,
    pk: selectedAllocation,
    fields: editAllocationFields,
    title: t`Edit Allocation`,
    onFormSuccess: () => table.refreshTable()
  });

  const deleteAllocation = useDeleteApiFormModal({
    url: ApiEndpoints.sales_order_allocation_list,
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
      // Do not allow "shipped" items to be manipulated
      const isShipped = !!record.shipment_detail?.shipment_date;

      return [
        RowEditAction({
          tooltip: t`Edit Allocation`,
          hidden:
            isShipped ||
            !allowEdit ||
            !user.hasChangeRole(UserRoles.sales_order),
          onClick: () => {
            setSelectedAllocation(record.pk);
            setSelectedShipment(record.shipment);
            editAllocation.open();
          }
        }),
        {
          title: t`Remove`,
          tooltip: t`Remove allocated stock`,
          icon: <IconCircleX />,
          color: 'red',
          hidden:
            isShipped ||
            !allowEdit ||
            !user.hasDeleteRole(UserRoles.sales_order),
          onClick: () => {
            setSelectedAllocation(record.pk);
            deleteAllocation.open();
          }
        },
        RowViewAction({
          tooltip: t`View Shipment`,
          title: t`View Shipment`,
          hidden: !record.shipment || !!shipmentId,
          modelId: record.shipment,
          modelType: ModelType.salesordershipment,
          navigate: navigate
        })
      ];
    },
    [allowEdit, shipmentId, user]
  );

  const stockOperationProps: StockOperationProps = useMemo(() => {
    // Extract stock items from the selected records
    // Note that the table is actually a list of SalesOrderAllocation instances,
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

  // A subset of the selected allocations, which can be assigned to a shipment
  const nonShippedAllocationIds: number[] = useMemo(() => {
    // Only allow allocations which have not been shipped
    return (
      table.selectedRecords?.filter((record) => {
        return !record.shipment_detail?.shipment_date;
      }) ?? []
    ).map((record: any) => record.pk);
  }, [table.selectedRecords]);

  const setShipment = useBulkEditApiFormModal({
    url: ApiEndpoints.sales_order_allocation_list,
    items: nonShippedAllocationIds,
    title: t`Assign to Shipment`,
    fields: {
      shipment: {
        filters: {
          order: orderId,
          shipped: false
        }
      }
    },
    onFormSuccess: table.refreshTable
  });

  const tableActions = useMemo(() => {
    return [
      stockAdjustActions.dropdown,
      <ActionButton
        tooltip={t`Assign to shipment`}
        icon={<IconTruckDelivery />}
        onClick={() => {
          setShipment.open();
        }}
        disabled={nonShippedAllocationIds.length == 0}
        hidden={
          !orderId || !allowEdit || !user.hasChangeRole(UserRoles.sales_order)
        }
        // TODO: Hide if order is already shipped
      />
    ];
  }, [
    allowEdit,
    nonShippedAllocationIds,
    orderId,
    user,
    stockAdjustActions.dropdown
  ]);

  return (
    <>
      {setShipment.modal}
      {editAllocation.modal}
      {deleteAllocation.modal}
      {!isSubTable && stockAdjustActions.modals.map((modal) => modal.modal)}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.sales_order_allocation_list)}
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
            shipment: shipmentId,
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
          modelType: modelTarget ?? ModelType.salesorder
        }}
      />
    </>
  );
}
