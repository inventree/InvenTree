import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { useTableRefresh } from '../../../hooks/TableRefresh';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Stock location table
 */
export function StockLocationTable({ params = {} }: { params?: any }) {
  const { tableKey, refreshTable } = useTableRefresh('stocklocation');

  const navigate = useNavigate();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Name`,
        switchable: false
      },
      {
        accessor: 'description',
        title: t`Description`,
        switchable: true
      },
      {
        accessor: 'pathstring',
        title: t`Path`,
        sortable: true,
        switchable: true
      },
      {
        accessor: 'items',
        title: t`Stock Items`,
        switchable: true,
        sortable: true
      },
      {
        accessor: 'structural',
        title: t`Structural`,
        switchable: true,
        sortable: true,
        render: (record: any) => (record.structural ? 'Y' : 'N')
        // TODO: custom 'true / false' label,
      },
      {
        accessor: 'external',
        title: t`External`,
        switchable: true,
        sortable: true,
        render: (record: any) => (record.structural ? 'Y' : 'N')
        // TODO: custom 'true / false' label,
      }
    ];
  }, [params]);

  return (
    <InvenTreeTable
      url="stock/location/"
      tableKey={tableKey}
      columns={tableColumns}
      props={{
        enableDownload: true,
        params: params,
        onRowClick: (record) => {
          navigate(`/stock/location/${record.pk}`);
        }
        // TODO: allow for "tree view" with cascade
      }}
    />
  );
}
