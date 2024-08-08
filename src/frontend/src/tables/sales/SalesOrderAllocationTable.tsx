import { useCallback, useMemo } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

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
    return [];
  }, []);

  const rowActions = useCallback(
    (record: any) => {
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
            stock_detail: true,
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
