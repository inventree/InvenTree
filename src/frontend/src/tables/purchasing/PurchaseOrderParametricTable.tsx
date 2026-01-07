import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { type ReactNode, useMemo } from 'react';
import {
  CompanyColumn,
  DescriptionColumn,
  ReferenceColumn
} from '../ColumnRenderers';
import {
  AssignedToMeFilter,
  OrderStatusFilter,
  OutstandingFilter,
  OverdueFilter,
  ProjectCodeFilter,
  ResponsibleFilter
} from '../Filter';
import ParametricDataTable from '../general/ParametricDataTable';

export default function PurchaseOrderParametricTable({
  queryParams
}: {
  queryParams?: Record<string, any>;
}): ReactNode {
  const customColumns: TableColumn[] = useMemo(() => {
    return [
      ReferenceColumn({
        switchable: false
      }),
      {
        accessor: 'supplier__name',
        title: t`Supplier`,
        sortable: true,
        render: (record: any) => (
          <CompanyColumn company={record.supplier_detail} />
        )
      },
      DescriptionColumn({})
    ];
  }, []);

  const customFilters: TableFilter[] = useMemo(() => {
    return [
      OrderStatusFilter({ model: ModelType.purchaseorder }),
      OutstandingFilter(),
      OverdueFilter(),
      AssignedToMeFilter(),
      ProjectCodeFilter(),
      ResponsibleFilter()
    ];
  }, []);

  return (
    <ParametricDataTable
      modelType={ModelType.purchaseorder}
      endpoint={ApiEndpoints.purchase_order_list}
      customColumns={customColumns}
      customFilters={customFilters}
      queryParams={{
        ...queryParams,
        supplier_detail: true
      }}
    />
  );
}
