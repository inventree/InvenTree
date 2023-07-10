import { Trans } from '@lingui/macro';
import { t } from '@lingui/macro';

import { useToggle } from '@mantine/hooks';

import { InvenTreeTable } from './InvenTreeTable';
import { ThumbnailHoverCard } from '../items/Thumbnail';
import { shortenString } from '../../functions/tables';
import { Group } from '@mantine/core';

import { DeleteButton } from '../items/DeleteButton';
import { EditButton } from '../items/EditButton';

/*
 * Load a table of stock items
 */
export function StockTable({
    params={}
}: {
    params?: any;
}) {

  const [editing, setEditing] = useToggle([false, true] as const);

    let tableParams = Object.assign({}, params);

    // Add required query parameters
    tableParams.part_detail = true;
    tableParams.location_detail = true;

    return <InvenTreeTable
        url='stock/'
        params={tableParams}
        tableKey='stock-table'
        allowSelection
        columns={[
          {
            accessor: 'part',
            sortable: true,
            title: t`Part`,
            render: function(record: any) {
              let part = record.part_detail;
              return <ThumbnailHoverCard
                src={part.thumbnail || part.image}
                text={part.name}
                link=""
              />;
            }
          },
          {
            accessor: 'part_detail.description',
            sortable: false,
            title: t`Description`,
          },
          {
            accessor: 'quantity',
            sortable: true,
            title: t`Stock`,
            // TODO: Custom renderer for stock quantity
          },
          {
            accessor: 'status',
            sortable: true,
            switchable: true,
            title: t`Status`,
            // TODO: Custom renderer for stock status label
          },
          {
            accessor: 'batch',
            sortable: true,
            switchable: true,
            title: t`Batch`,
          },
          {
            accessor: 'location',
            sortable: true,
            switchable: true,
            title: t`Location`,
            render: function(record: any) {
              // TODO: Custom renderer for location
              return record.location; 
            }
          },
          // TODO: stocktake column
          // TODO: expiry date
          // TODO: last updated
          // TODO: purchase order
          // TODO: Supplier part
          // TODO: purchase price
          // TODO: stock value
          // TODO: packaging
          // TODO: notes
          // TODO: actions
          {
            accessor: 'actions',
            title: t`Actions`,
            sortable: false,
            render: function(record: any) {
              return <Group position="right" spacing={5} noWrap={true}>
                {EditButton(setEditing, editing)}
                {DeleteButton()}
              </Group>;
            },
          }
        ]}
    />;
}
