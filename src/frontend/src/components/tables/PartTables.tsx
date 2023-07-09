import { Text } from '@mantine/core';
import { DataTable } from 'mantine-datatable';

import { InvenTreeTable } from './InvenTreeTable';

export function PartTable() {
    return <InvenTreeTable
        url='part/'
        params
        paginated={true}
        pageSize={25}
        tableKey='part-table'
        columns={[
          {
            accessor: 'name',
            sortable: true,
          },
          {
            accessor: 'IPN',
            sortable: true,
          },
          {
            accessor: 'units',
            sortable: true,
          },
          {
            accessor: 'description',
            sortable: true,
          },
        ]}
    />;

}