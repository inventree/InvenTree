import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * PartCategoryTable - Displays a table of part categories
 */
export function PartCategoryTable({ params = {} }: { params?: any }) {
  const navigate = useNavigate();

  const { tableKey, refreshTable } = useTableRefresh('partcategory');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Name`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'description',
        title: t`Description`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'pathstring',
        title: t`Path`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'part_count',
        title: t`Parts`,
        sortable: true,
        switchable: true
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.category_list)}
      tableKey={tableKey}
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
