import { t } from '@lingui/macro';
import { Trans } from '@lingui/macro';

import { shortenString } from '../../functions/tables';

import { InvenTreeTable } from './InvenTreeTable';

export function PartTable({
    params={}
  }: {
    params?: any;
  }) {

    let tableParams = Object.assign({}, params);
    
    // Add required query parmeters
    tableParams.category_detail = true;

    return <InvenTreeTable
        url='part/'
        params={tableParams}
        tableKey='part-table'
        columns={[
          {
            accessor: 'name',
            sortable: true,
            title: t`Part`
          },
          {
            accessor: 'IPN',
            title: t`IPN`,
            sortable: true,
          },
          {
            accessor: 'units',
            sortable: true,
            title: t`Units`
          },
          {
            accessor: 'description',
            title: t`Description`,
            sortable: true,
          },
          {
            accessor: 'category',
            title: t`Category`,
            sortable: true,
            render: function(record) {
              return shortenString({
                str: record.category_detail.pathstring,
              });
            }
          },
          {
            accessor: 'total_in_stock',
            title: t`Stock`,
            sortable: true,
          }
        ]}
    />;

}