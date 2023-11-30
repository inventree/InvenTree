import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { ReactNode, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { formatCurrency, renderDate } from '../../../defaults/formatters';
import { ApiPaths } from '../../../enums/ApiEndpoints';
import { ModelType } from '../../../enums/ModelType';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import { TableColumn } from '../Column';
import { StatusColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { TableHoverCard } from '../TableHoverCard';
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

      title: t`Description`
    },
    {
      accessor: 'quantity',
      sortable: true,
      title: t`Stock`,
      render: (record) => {
        // TODO: Push this out into a custom renderer
        let quantity = record?.quantity ?? 0;
        let allocated = record?.allocated ?? 0;
        let available = quantity - allocated;
        let text = quantity;
        let part = record?.part_detail ?? {};
        let extra: ReactNode[] = [];
        let color = undefined;

        if (record.serial && quantity == 1) {
          text = `# ${record.serial}`;
        }

        if (record.is_building) {
          color = 'blue';
          extra.push(
            <Text
              key="production"
              size="sm"
            >{t`This stock item is in production`}</Text>
          );
        }

        if (record.sales_order) {
          extra.push(
            <Text
              key="sales-order"
              size="sm"
            >{t`This stock item has been assigned to a sales order`}</Text>
          );
        }

        if (record.customer) {
          extra.push(
            <Text
              key="customer"
              size="sm"
            >{t`This stock item has been assigned to a customer`}</Text>
          );
        }

        if (record.belongs_to) {
          extra.push(
            <Text
              key="belongs-to"
              size="sm"
            >{t`This stock item is installed in another stock item`}</Text>
          );
        }

        if (record.consumed_by) {
          extra.push(
            <Text
              key="consumed-by"
              size="sm"
            >{t`This stock item has been consumed by a build order`}</Text>
          );
        }

        if (record.expired) {
          extra.push(
            <Text
              key="expired"
              size="sm"
            >{t`This stock item has expired`}</Text>
          );
        } else if (record.stale) {
          extra.push(
            <Text key="stale" size="sm">{t`This stock item is stale`}</Text>
          );
        }

        if (allocated > 0) {
          if (allocated >= quantity) {
            color = 'orange';
            extra.push(
              <Text
                key="fully-allocated"
                size="sm"
              >{t`This stock item is fully allocated`}</Text>
            );
          } else {
            extra.push(
              <Text
                key="partially-allocated"
                size="sm"
              >{t`This stock item is partially allocated`}</Text>
            );
          }
        }

        if (available != quantity) {
          if (available > 0) {
            extra.push(
              <Text key="available" size="sm" color="orange">
                {t`Available` + `: ${available}`}
              </Text>
            );
          } else {
            extra.push(
              <Text
                key="no-stock"
                size="sm"
                color="red"
              >{t`No stock available`}</Text>
            );
          }
        }

        if (quantity <= 0) {
          color = 'red';
          extra.push(
            <Text
              key="depleted"
              size="sm"
            >{t`This stock item has been depleted`}</Text>
          );
        }

        return (
          <TableHoverCard
            value={
              <Group spacing="xs" position="left" noWrap={true}>
                <Text color={color}>{text}</Text>
                {part.units && (
                  <Text size="xs" color={color}>
                    [{part.units}]
                  </Text>
                )}
              </Group>
            }
            title={t`Stock Information`}
            extra={extra}
          />
        );
      }
    },
    StatusColumn(ModelType.stockitem),
    {
      accessor: 'batch',
      sortable: true,

      title: t`Batch`
    },
    {
      accessor: 'location',
      sortable: true,

      title: t`Location`,
      render: function (record: any) {
        // TODO: Custom renderer for location
        // TODO: Note, if not "In stock" we don't want to display the actual location here
        return record?.location_detail?.pathstring ?? record.location ?? '-';
      }
    },
    // TODO: stocktake column
    {
      accessor: 'expiry_date',
      sortable: true,
      title: t`Expiry Date`,
      switchable: true,
      render: (record: any) => renderDate(record.expiry_date)
    },
    {
      accessor: 'updated',
      sortable: true,
      title: t`Last Updated`,
      switchable: true,
      render: (record: any) => renderDate(record.updated)
    },
    // TODO: purchase order
    // TODO: Supplier part
    {
      accessor: 'purchase_price',
      sortable: true,
      title: t`Purchase Price`,
      switchable: true,
      render: (record: any) =>
        formatCurrency(record.purchase_price, {
          currency: record.purchase_price_currency
        })
    }
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
export function StockItemTable({
  wait = false,
  params = {}
}: {
  wait: boolean;
  params?: any;
}) {
  let tableColumns = useMemo(() => stockItemTableColumns(), []);
  let tableFilters = useMemo(() => stockItemTableFilters(), []);

  const table = useTable('stockitems');

  const navigate = useNavigate();

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.stock_item_list)}
      wait={wait}
      tableState={table}
      columns={tableColumns}
      props={{
        enableDownload: true,
        enableSelection: true,
        customFilters: tableFilters,
        onRowClick: (record) => navigate(`/stock/item/${record.pk}`),
        params: {
          ...params,
          part_detail: true,
          location_detail: true,
          supplier_part_detail: true
        }
      }}
    />
  );
}
