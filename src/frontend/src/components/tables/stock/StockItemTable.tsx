import { t } from '@lingui/macro';
import { Group } from '@mantine/core';
import { IconEdit, IconTrash } from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';

import { notYetImplemented } from '../../../functions/notifications';
import { ActionButton } from '../../items/ActionButton';
import { ThumbnailHoverCard } from '../../items/Thumbnail';
import { TableColumn } from '../Column';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from './../InvenTreeTable';

/**
 * Construct a list of columns for the stock item table
 */
function stockItemTableColumns(): TableColumn[] {
  return [
    {
      accessor: 'part',
      sortable: true,
      title: t`Part`,
      render: function (record: any) {
        let part = record.part_detail;
        return (
          <ThumbnailHoverCard
            src={part.thumbnail || part.image}
            text={part.name}
            link=""
          />
        );
      }
    },
    {
      accessor: 'part_detail.description',
      sortable: false,
      switchable: true,
      title: t`Description`
    },
    {
      accessor: 'quantity',
      sortable: true,
      title: t`Stock`
      // TODO: Custom renderer for stock quantity
    },
    {
      accessor: 'status',
      sortable: true,
      switchable: true,
      filter: true,
      title: t`Status`
      // TODO: Custom renderer for stock status label
    },
    {
      accessor: 'batch',
      sortable: true,
      switchable: true,
      title: t`Batch`
    },
    {
      accessor: 'location',
      sortable: true,
      switchable: true,
      title: t`Location`,
      render: function (record: any) {
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
    {
      accessor: 'actions',
      title: t`Actions`,
      sortable: false,
      render: function (record: any) {
        return (
          <Group position="right" spacing={5} noWrap={true}>
            {/* {EditButton(setEditing, editing)} */}
            {/* {DeleteButton()} */}
            <ActionButton
              color="green"
              icon={<IconEdit />}
              tooltip="Edit stock item"
              onClick={() => notYetImplemented()}
            />
            <ActionButton
              color="red"
              tooltip="Delete stock item"
              icon={<IconTrash />}
              onClick={() => notYetImplemented()}
            />
          </Group>
        );
      }
    }
  ];
}

/**
 * Return a set of parameters for the stock item table
 */
function stockItemTableParams(params: any): any {
  return {
    ...params,
    part_detail: true,
    location_detail: true
  };
}

/**
 * Construct a list of available filters for the stock item table
 */
function stockItemTableFilters(): TableFilter[] {
  return [
    {
      name: 'test_filter',
      label: t`Test Filter`,
      description: t`This is a test filter`,
      type: 'choice',
      choiceFunction: () => [
        { value: '1', label: 'One' },
        { value: '2', label: 'Two' },
        { value: '3', label: 'Three' }
      ]
    }
  ];
}

/*
 * Load a table of stock items
 */
export function StockItemTable({ params = {} }: { params?: any }) {
  let tableParams = useMemo(() => stockItemTableParams(params), []);
  let tableColumns = useMemo(() => stockItemTableColumns(), []);
  let tableFilters = useMemo(() => stockItemTableFilters(), []);

  return (
    <InvenTreeTable
      url="stock/"
      tableKey="stock-table"
      enableDownload
      enableSelection
      params={tableParams}
      columns={tableColumns}
      customFilters={tableFilters}
    />
  );
}
