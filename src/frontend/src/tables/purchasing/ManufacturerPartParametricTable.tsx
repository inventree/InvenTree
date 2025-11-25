import { ApiEndpoints, ModelType } from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { type ReactNode, useMemo } from 'react';
import ParametricDataTable from '../general/ParametricDataTable';

export default function ManufacturerPartParametricTable({
  queryParams
}: {
  queryParams?: Record<string, any>;
}): ReactNode {
  const customColumns: TableColumn[] = useMemo(() => {
    return [];
  }, []);

  const customFilters: TableFilter[] = useMemo(() => {
    return [];
  }, []);

  return (
    <ParametricDataTable
      modelType={ModelType.manufacturerpart}
      endpoint={ApiEndpoints.manufacturer_part_list}
      customColumns={customColumns}
      customFilters={customFilters}
      queryParams={{
        ...queryParams,
        part_detail: true,
        manufacturer_detail: true
      }}
    />
  );
}
