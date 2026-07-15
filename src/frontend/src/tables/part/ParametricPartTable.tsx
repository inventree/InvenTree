import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { useMemo, useRef } from 'react';
import { PartCreationMenu } from '../../components/items/PartCreationMenu';
import {
  DescriptionColumn,
  PartColumn
} from '../../components/tables/ColumnRenderers';
import ParametricDataTable from '../general/ParametricDataTable';
import { PartTableFilters } from './PartTableFilters';

export default function ParametricPartTable({
  categoryId,
  enableImport = true
}: Readonly<{
  categoryId?: any;
  enableImport?: boolean;
}>) {
  const tableRefreshRef = useRef<() => void>(null!);

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

  const tableActions = useMemo(
    () => [
      <PartCreationMenu
        key='part-creation-menu'
        categoryId={categoryId}
        enableImport={enableImport}
        refreshRef={tableRefreshRef}
      />
    ],
    [categoryId, enableImport]
  );

  return (
    <ParametricDataTable
      modelType={ModelType.part}
      relatedModel={'category'}
      relatedModelId={categoryId}
      endpoint={ApiEndpoints.part_list}
      customColumns={customColumns}
      customFilters={customFilters}
      customActions={tableActions}
      refreshRef={tableRefreshRef}
      queryParams={{
        category: categoryId,
        cascade: true,
        category_detail: true
      }}
    />
  );
}
