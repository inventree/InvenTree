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

export default function SalesOrderParametricTable({
  queryParams
}: {
  queryParams?: Record<string, any>;
}): ReactNode {
  const customColumns: TableColumn[] = useMemo(() => {
    return [
      ReferenceColumn({ switchable: false }),
      {
        accessor: 'customer__name',
        title: t`Customer`,
        sortable: true,
        render: (record: any) => (
          <CompanyColumn company={record.customer_detail} />
        )
      },
      DescriptionColumn({})
    ];
  }, []);

  const customFilters: TableFilter[] = useMemo(() => {
    return [
      OrderStatusFilter({ model: ModelType.salesorder }),
      OutstandingFilter(),
      OverdueFilter(),
      AssignedToMeFilter(),
      ProjectCodeFilter(),
      ResponsibleFilter()
    ];
  }, []);

  return (
    <ParametricDataTable
      modelType={ModelType.salesorder}
      endpoint={ApiEndpoints.sales_order_list}
      customColumns={customColumns}
      customFilters={customFilters}
      queryParams={{
        ...queryParams,
        customer_detail: true
      }}
    />
  );
}
