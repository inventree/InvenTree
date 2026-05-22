import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { type ReactNode, useMemo } from 'react';
import { DescriptionColumn, ReferenceColumn } from '../ColumnRenderers';
import {
  AssignedToMeFilter,
  OrderStatusFilter,
  OutstandingFilter,
  OverdueFilter,
  ProjectCodeFilter,
  ResponsibleFilter
} from '../Filter';
import ParametricDataTable from '../general/ParametricDataTable';

export default function TransferOrderParametricTable({
  queryParams
}: {
  queryParams?: Record<string, any>;
}): ReactNode {
  const customColumns: TableColumn[] = useMemo(() => {
    return [ReferenceColumn({ switchable: false }), DescriptionColumn({})];
  }, []);

  const customFilters: TableFilter[] = useMemo(() => {
    return [
      OrderStatusFilter({ model: ModelType.transferorder }),
      OutstandingFilter(),
      OverdueFilter(),
      AssignedToMeFilter(),
      ProjectCodeFilter(),
      ResponsibleFilter()
    ];
  }, []);

  return (
    <ParametricDataTable
      modelType={ModelType.transferorder}
      endpoint={ApiEndpoints.transfer_order_list}
      customColumns={customColumns}
      customFilters={customFilters}
      queryParams={{
        ...queryParams
      }}
    />
  );
}
