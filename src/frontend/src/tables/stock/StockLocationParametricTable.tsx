import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import type { TableColumn } from '@lib/types/Tables';
import { Group } from '@mantine/core';
import { type ReactNode, useMemo } from 'react';
import { ApiIcon } from '../../components/items/ApiIcon';
import { DescriptionColumn } from '../ColumnRenderers';
import ParametricDataTable from '../general/ParametricDataTable';

export default function StockLocationParametricTable({
  queryParams
}: {
  queryParams?: Record<string, any>;
}): ReactNode {
  const customColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        switchable: false,
        render: (record: any) => (
          <Group gap='xs'>
            {record.icon && <ApiIcon name={record.icon} />}
            {record.name}
          </Group>
        )
      },
      DescriptionColumn({}),
      {
        accessor: 'pathstring',
        sortable: true
      }
    ];
  }, []);

  return (
    <ParametricDataTable
      modelType={ModelType.stocklocation}
      endpoint={ApiEndpoints.stock_location_list}
      customColumns={customColumns}
      queryParams={{
        ...queryParams
      }}
    />
  );
}
