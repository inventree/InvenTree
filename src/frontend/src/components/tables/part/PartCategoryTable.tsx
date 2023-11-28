import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../Column';
import { DescriptionColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * PartCategoryTable - Displays a table of part categories
 */
export function PartCategoryTable({ params = {} }: { params?: any }) {
  const navigate = useNavigate();

  const table = useTable('partcategory');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Name`,
        sortable: true,
        switchable: false
      },
      DescriptionColumn(),
      {
        accessor: 'pathstring',
        title: t`Path`,
        sortable: false
      },
      {
        accessor: 'part_count',
        title: t`Parts`,
        sortable: true
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.category_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        enableDownload: true,
        enableSelection: true,
        params: {
          ...params
        },
        onRowClick: (record, index, event) => {
          navigate(`/part/category/${record.pk}`);
        }
      }}
    />
  );
}
