import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { useMemo } from 'react';
import { DescriptionColumn, PartColumn } from '../ColumnRenderers';
import ParametricDataTable from '../general/ParametricDataTable';
import { PartTableFilters } from './PartTableFilters';

export default function ParametricPartTable({
  categoryId
}: Readonly<{
  categoryId?: any;
}>) {
  const customFilters: TableFilter[] = useMemo(() => PartTableFilters(), []);

  const customColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({
        part: '',
        switchable: false
      }),
      DescriptionColumn({
        defaultVisible: false
      }),
      {
        accessor: 'IPN',
        sortable: true,
        defaultVisible: false
      },
      {
        accessor: 'total_in_stock',
        sortable: true
      }
    ];
  }, []);

  return (
    <ParametricDataTable
      modelType={ModelType.part}
      relatedModel={'category'}
      relatedModelId={categoryId}
      endpoint={ApiEndpoints.part_list}
      customColumns={customColumns}
      customFilters={customFilters}
      queryParams={{
        category: categoryId,
        cascade: true,
        category_detail: true
      }}
    />
  );
}
