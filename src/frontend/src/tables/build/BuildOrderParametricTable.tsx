import { ApiEndpoints, ModelType } from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { type ReactNode, useMemo } from 'react';
import {
  DescriptionColumn,
  PartColumn,
  ReferenceColumn
} from '../ColumnRenderers';
import { OrderStatusFilter, OutstandingFilter } from '../Filter';
import ParametricDataTable from '../general/ParametricDataTable';

export default function BuildOrderParametricTable({
  queryParams
}: {
  queryParams?: Record<string, any>;
}): ReactNode {
  const customColumns: TableColumn[] = useMemo(() => {
    return [
      ReferenceColumn({
        switchable: false
      }),
      PartColumn({
        part: 'part_detail',
        title: t`Part`
      }),
      DescriptionColumn({
        accessor: 'title'
      })
    ];
  }, []);

  const customFilters: TableFilter[] = useMemo(() => {
    return [OutstandingFilter(), OrderStatusFilter({ model: ModelType.build })];
  }, []);

  return (
    <ParametricDataTable
      modelType={ModelType.build}
      endpoint={ApiEndpoints.build_order_list}
      customColumns={customColumns}
      customFilters={customFilters}
      queryParams={{
        part_detail: true,
        ...queryParams
      }}
    />
  );
}
