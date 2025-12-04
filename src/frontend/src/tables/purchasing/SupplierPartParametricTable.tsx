import { ApiEndpoints, ModelType } from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { type ReactNode, useMemo } from 'react';
import { CompanyColumn, PartColumn } from '../ColumnRenderers';
import ParametricDataTable from '../general/ParametricDataTable';

export default function SupplierPartParametricTable({
  queryParams
}: {
  queryParams?: Record<string, any>;
}): ReactNode {
  const customColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({
        switchable: false,
        part: 'part_detail'
      }),
      {
        accessor: 'supplier',
        sortable: true,
        render: (record: any) => (
          <CompanyColumn company={record?.supplier_detail} />
        )
      },
      {
        accessor: 'SKU',
        title: t`Supplier Part`,
        sortable: true
      }
    ];
  }, []);

  const customFilters: TableFilter[] = useMemo(() => {
    return [];
  }, []);

  return (
    <ParametricDataTable
      modelType={ModelType.supplierpart}
      endpoint={ApiEndpoints.supplier_part_list}
      customColumns={customColumns}
      customFilters={customFilters}
      queryParams={{
        ...queryParams,
        part_detail: true,
        supplier_detail: true
      }}
    />
  );
}
