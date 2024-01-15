import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { YesNoButton } from '../../items/YesNoButton';
import { TableColumn } from '../Column';
import { DescriptionColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
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
        accessor: 'structural',
        title: t`Structural`,
        sortable: true,
        render: (record: any) => {
          return <YesNoButton value={record.structural} />;
        }
      },
      {
        accessor: 'part_count',
        title: t`Parts`,
        sortable: true
      }
    ];
  }, []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'cascade',
        label: t`Include Subcategories`,
        description: t`Include subcategories in results`
      },
      {
        name: 'structural',
        label: t`Structural`,
        description: t`Show structural categories`
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
        customFilters: tableFilters,
        onRowClick: (record, index, event) => {
          navigate(`/part/category/${record.pk}`);
        }
      }}
    />
  );
}
