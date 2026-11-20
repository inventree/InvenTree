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
} from '../../components/tables/ColumnRenderers';
import ParametricDataTable from '../general/ParametricDataTable';
import RepairOrderFilters from './RepairOrderFilters';

export default function RepairOrderParametricTable({
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
    return RepairOrderFilters({ includeDateFilters: true });
  }, []);

  return (
    <ParametricDataTable
      modelType={ModelType.repairorder}
      endpoint={ApiEndpoints.repair_order_list}
      customColumns={customColumns}
      customFilters={customFilters}
      queryParams={{
        ...queryParams,
        customer_detail: true
      }}
    />
  );
}
