import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { notYetImplemented } from '../../../functions/notifications';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import { TableColumn } from '../Column';
import { TableFilter } from '../Filter';
import { RowAction } from '../RowActions';
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
        let part = record.part_detail ?? {};
        return (
          <Group spacing="xs" noWrap={true}>
            <Thumbnail
              src={part?.thumbnail || part?.image}
              alt={part?.name}
              size={24}
            />
            <Text>{part?.full_name}</Text>
          </Group>
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
    }
    // TODO: stocktake column
    // TODO: expiry date
    // TODO: last updated
    // TODO: purchase order
    // TODO: Supplier part
    // TODO: purchase price
    // TODO: stock value
    // TODO: packaging
    // TODO: notes
  ];
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
  let tableColumns = useMemo(() => stockItemTableColumns(), []);
  let tableFilters = useMemo(() => stockItemTableFilters(), []);

  const { tableKey, refreshTable } = useTableRefresh('stockitem');

  function stockItemRowActions(record: any): RowAction[] {
    let actions: RowAction[] = [];

    actions.push({
      title: t`Edit`,
      onClick: () => {
        notYetImplemented();
      }
    });

    return actions;
  }

  const navigate = useNavigate();

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.stock_item_list)}
      tableKey={tableKey}
      columns={tableColumns}
      props={{
        enableDownload: true,
        enableSelection: true,
        customFilters: tableFilters,
        rowActions: stockItemRowActions,
        onRowClick: (record) => navigate(`/stock/item/${record.pk}`),
        params: {
          ...params,
          part_detail: true,
          location_detail: true
        }
      }}
    />
  );
}
