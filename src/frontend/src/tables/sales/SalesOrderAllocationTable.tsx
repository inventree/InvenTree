import { t } from '@lingui/macro';
import { useCallback, useMemo } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import {
  LocationColumn,
  PartColumn,
  ReferenceColumn,
  StatusColumn
} from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction } from '../RowActions';

export default function SalesOrderAllocationTable({
  partId,
  stockId,
  orderId,
  showPartInfo,
  showOrderInfo,
  allowEdit,
  modelTarget,
  modelField
}: {
  partId?: number;
  stockId?: number;
  orderId?: number;
  showPartInfo?: boolean;
  showOrderInfo?: boolean;
  allowEdit?: boolean;
  modelTarget?: ModelType;
  modelField?: string;
}) {
  const user = useUserState();
  const table = useTable('salesorderallocations');

  const tableFilters: TableFilter[] = useMemo(() => {
    return [];
  }, []);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      ReferenceColumn({
        accessor: 'order_detail.reference',
        title: t`Sales Order`,
        switchable: false,
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
        render: (record: any) => PartColumn(record.part_detail)
      },
      {
        accessor: 'quantity',
        title: t`Allocated Quantity`,
        sortable: true
      },
      {
        accessor: 'serial',
        title: t`Serial Number`,
        sortable: false,
        switchable: true,
        render: (record: any) => record?.item_detail?.serial
      },
      {
        accessor: 'batch',
        title: t`Batch Code`,
        sortable: false,
        switchable: true,
        render: (record: any) => record?.item_detail?.batch
      },
      {
        accessor: 'available',
        title: t`Available Quantity`,
        render: (record: any) => record?.item_detail?.quantity
      },
      LocationColumn({
        accessor: 'location_detail',
        switchable: true,
        sortable: true
      })
    ];
  }, []);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [];
    },
    [user]
  );

  return (
    <>
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
            stock_item: stockId
          },
          rowActions: rowActions,
          tableFilters: tableFilters,
          modelField: modelField ?? 'order',
          modelType: modelTarget ?? ModelType.salesorder
        }}
      />
    </>
  );
}
