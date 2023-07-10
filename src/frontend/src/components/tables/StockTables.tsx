import { Trans } from '@lingui/macro';

import { InvenTreeTable } from './InvenTreeTable';

/*
 * Load a table of stock items
 */
export function StockTable({
    params={}
}: {
    params?: any;
}) {

    let tableParams = Object.assign({}, params);

    // Add required query parameters
    params.part_detail = true;

    return <InvenTreeTable
        url='stock/'
        params={tableParams}
        tableKey='stock-table'
        columns={[
          {
            accessor: 'quantity',
            sortable: true,
          },
        ]}
    />;
}
