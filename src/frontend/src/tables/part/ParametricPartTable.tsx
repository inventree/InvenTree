import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { useMemo } from 'react';
import { DescriptionColumn, PartColumn } from '../ColumnRenderers';
import ParametricDataTable from '../general/ParametricDataTable';

export default function ParametricPartTable({
  categoryId
}: Readonly<{
  categoryId?: any;
}>) {
  const customFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'active',
        label: t`Active`,
        description: t`Show active parts`
      },
      {
        name: 'locked',
        label: t`Locked`,
        description: t`Show locked parts`
      },
      {
        name: 'assembly',
        label: t`Assembly`,
        description: t`Show assembly parts`
      }
    ];
  }, []);

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
