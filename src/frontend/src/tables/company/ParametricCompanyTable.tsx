import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
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
      queryParams={{
        ...queryParams
      }}
    />
  );
}
