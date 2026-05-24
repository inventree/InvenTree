import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { useMemo } from 'react';
import { CompanyColumn, DescriptionColumn } from '../ColumnRenderers';
import ParametricDataTable from '../general/ParametricDataTable';

export default function ParametricCompanyTable({
  queryParams
}: {
  queryParams?: any;
}) {
  const customFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'active',
        label: t`Active`,
        description: t`Show active companies`
      }
    ];
  }, []);

  const customColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Company`,
        sortable: true,
        switchable: false,
        render: (record: any) => {
          return <CompanyColumn company={record} />;
        }
      },
      DescriptionColumn({})
    ];
  }, []);

  return (
    <ParametricDataTable
      modelType={ModelType.company}
      endpoint={ApiEndpoints.company_list}
      customColumns={customColumns}
      customFilters={customFilters}
      queryParams={{
        ...queryParams
      }}
    />
  );
}
