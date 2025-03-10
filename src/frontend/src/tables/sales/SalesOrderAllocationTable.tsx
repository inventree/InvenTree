import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { formatDate } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useSalesOrderAllocationFields } from '../../forms/SalesOrderForms';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import {
  LocationColumn,
  PartColumn,
  ReferenceColumn,
  StatusColumn
} from '../ColumnRenderers';
import type { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

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
      }
    ];

    if (!!partId) {
      filters.push({
        name: 'include_variants',
        type: 'boolean',
        label: t`Include Variants`,
        description: t`Include orders for part variants`
      });
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
      {
        accessor: 'order_detail.description',
        title: t`Description`,
        hidden: showOrderInfo != true
      },
      StatusColumn({
        accessor: 'order_detail.status',
        model: ModelType.salesorder,
        title: t`Order Status`,
        hidden: showOrderInfo != true
      }),
      {
        accessor: 'part',
        hidden: showPartInfo != true,
        title: t`Part`,
        sortable: true,
        switchable: false,
        render: (record: any) => PartColumn({ part: record.part_detail })
      },
      {
        accessor: 'part_detail.description',
        title: t`Description`,
        hidden: showPartInfo != true,
        sortable: false
      },
      {
        accessor: 'part_detail.IPN',
        title: t`IPN`,
        hidden: showPartInfo != true,
        sortable: false
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
    title: t`Delete Allocation`,
    onFormSuccess: () => table.refreshTable()
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      // Do not allow "shipped" items to be manipulated
      const isShipped = !!record.shipment_detail?.shipment_date;

      if (isShipped || !allowEdit) {
        return [];
      }

      return [
        RowEditAction({
          tooltip: t`Edit Allocation`,
          onClick: () => {
            setSelectedAllocation(record.pk);
            setSelectedShipment(record.shipment);
            editAllocation.open();
          }
        }),
        RowDeleteAction({
          tooltip: t`Delete Allocation`,
          onClick: () => {
            setSelectedAllocation(record.pk);
            deleteAllocation.open();
          }
        })
      ];
    },
    [allowEdit, user]
  );

  const tableActions = useMemo(() => {
    if (!allowEdit) {
      return [];
    }

    return [];
  }, [allowEdit, user]);

  return (
    <>
      {editAllocation.modal}
      {deleteAllocation.modal}
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
          minHeight: isSubTable ? 100 : undefined,
          rowActions: rowActions,
          tableActions: tableActions,
          tableFilters: tableFilters,
          modelField: modelField ?? 'order',
          modelType: modelTarget ?? ModelType.salesorder
        }}
      />
    </>
  );
}
