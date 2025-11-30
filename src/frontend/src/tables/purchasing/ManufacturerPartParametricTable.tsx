import { ApiEndpoints, ModelType } from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { type ReactNode, useMemo } from 'react';
import { CompanyColumn, PartColumn } from '../ColumnRenderers';
import ParametricDataTable from '../general/ParametricDataTable';

export default function ManufacturerPartParametricTable({
  queryParams
}: {
  queryParams?: Record<string, any>;
}): ReactNode {
  const customColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({
        switchable: false
      }),
      {
        accessor: 'part_detail.IPN',
        title: t`IPN`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'manufacturer',
        sortable: true,
        render: (record: any) => (
          <CompanyColumn company={record?.manufacturer_detail} />
        )
      },
      {
        accessor: 'MPN',
        title: t`MPN`,
        sortable: true
      }
    ];
  }, []);

  const customFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'part_active',
        label: t`Active Part`,
        description: t`Show manufacturer parts for active internal parts.`,
        type: 'boolean'
      },
      {
        name: 'manufacturer_active',
        label: t`Active Manufacturer`,
        description: t`Show manufacturer parts for active manufacturers.`,
        type: 'boolean'
      }
    ];
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
