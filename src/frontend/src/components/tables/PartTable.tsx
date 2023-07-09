import { Text } from '@mantine/core';
import { DataTable } from 'mantine-datatable';

export function PartTable() {
    return <DataTable 
        withBorder
        highlightOnHover
        records={[
          { id: 1, name: 'Joe Biden', bornIn: 1942, party: 'Democratic' },
          // more records...s
        ]}
        // define columns
        columns={[
          {
            accessor: 'id',
            // this column has a custom title
            title: '#',
            // right-align column
            textAlignment: 'right',
          },
          { accessor: 'name' },
          {
            accessor: 'party',
            // this column has custom cell data rendering
            render: ({ party }) => (
              <Text weight={700} color={party === 'Democratic' ? 'blue' : 'red'}>
                {party.slice(0, 3).toUpperCase()}
              </Text>
            ),
          },
          { accessor: 'bornIn' },
        ]}
      />;
}