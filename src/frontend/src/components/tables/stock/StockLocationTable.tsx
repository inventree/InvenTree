import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { useTableRefresh } from '../../../hooks/TableRefresh';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Stock location table
 */
export function StockLocationTable({ params = {} }: { params?: any }) {
  const { tableKey, refreshTable } = useTableRefresh('stocklocation');

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
        params: params
        // TODO: allow for "tree view" with cascade
      }}
    />
  );
}
