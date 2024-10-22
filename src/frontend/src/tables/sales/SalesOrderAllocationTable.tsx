import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { YesNoButton } from '../../components/buttons/YesNoButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useSalesOrderAllocationFields } from '../../forms/SalesOrderForms';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import {
  DateColumn,
  LocationColumn,
  PartColumn,
  ReferenceColumn,
  StatusColumn
} from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

export default function SalesOrderAllocationTable({
  partId,
  stockId,
  orderId,
  shipmentId,
  showPartInfo,
  showOrderInfo,
  allowEdit,
  modelTarget,
  modelField
}: Readonly<{
  partId?: number;
  stockId?: number;
  orderId?: number;
  shipmentId?: number;
  showPartInfo?: boolean;
  showOrderInfo?: boolean;
  allowEdit?: boolean;
  modelTarget?: ModelType;
  modelField?: string;
}>) {
  const user = useUserState();
  const table = useTable(
    !!partId ? 'salesorderallocations-part' : 'salesorderallocations'
  );

  const tableFilters: TableFilter[] = useMemo(() => {
    let filters: TableFilter[] = [
      {
        name: 'outstanding',
        label: t`Outstanding`,
        description: t`Show outstanding allocations`
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
        sortable: false
      },
      DateColumn({
        accessor: 'shipment_detail.shipment_date',
        title: t`Shipment Date`,
        switchable: true,
        sortable: false
      }),
      {
        accessor: 'shipment_date',
        title: t`Shipped`,
        switchable: true,
        sortable: false,
        render: (record: any) => (
          <YesNoButton value={!!record.shipment_detail?.shipment_date} />
        )
      }
    ];
  }, []);

  const [selectedAllocation, setSelectedAllocation] = useState<number>(0);

  const editAllocationFields = useSalesOrderAllocationFields({
    shipmentId: shipmentId
  });

  const editAllocation = useEditApiFormModal({
    url: ApiEndpoints.sales_order_allocation_list,
    pk: selectedAllocation,
    fields: editAllocationFields,
    title: t`Edit Allocation`,
    table: table
  });

  const deleteAllocation = useDeleteApiFormModal({
    url: ApiEndpoints.sales_order_allocation_list,
    pk: selectedAllocation,
    title: t`Delete Allocation`,
    table: table
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
            part: partId,
            order: orderId,
            shipment: shipmentId,
            item: stockId
          },
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
