import { Trans } from '@lingui/macro';

import { InvenTreeTable } from './InvenTreeTable';

export function PartTable() {
    return <InvenTreeTable
        url='part/'
        params
        tableKey='part-table'
        columns={[
          {
            accessor: 'name',
            sortable: true,
          },
          {
            accessor: 'IPN',
            title: 'IPN',
            sortable: true,
          },
          {
            accessor: 'units',
            sortable: true,
          },
          {
            accessor: 'description',
            title: <Trans>Description</Trans>,
            sortable: true,
          },
          {
            accessor: 'total_in_stock',
            title: <Trans>Stock</Trans>,
            sortable: true,
          }
        ]}
    />;

}