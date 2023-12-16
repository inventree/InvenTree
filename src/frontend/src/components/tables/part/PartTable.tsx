import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { ReactNode, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { formatPriceRange } from '../../../defaults/formatters';
import { ApiPaths } from '../../../enums/ApiEndpoints';
import { shortenString } from '../../../functions/tables';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import { TableColumn } from '../Column';
import { DescriptionColumn, LinkColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable, InvenTreeTableProps } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

/**
 * Construct a list of columns for the part table
 */
function partTableColumns(): TableColumn[] {
  return [
    {
      accessor: 'name',
      sortable: true,
      noWrap: true,
      title: t`Part`,
      render: function (record: any) {
        return (
          <Thumbnail
            src={record.thumbnail || record.image}
            alt={record.name}
            text={record.full_name}
          />
        );
      }
    },
    {
      accessor: 'IPN',
      title: t`IPN`,
      sortable: true
    },
    {
      accessor: 'units',
      sortable: true,
      title: t`Units`
    },
    DescriptionColumn(),
    {
      accessor: 'category',
      title: t`Category`,
      sortable: true,

      render: function (record: any) {
        // TODO: Link to the category detail page
        return shortenString({
          str: record.category_detail?.pathstring
        });
      }
    },
    {
      accessor: 'total_in_stock',
      title: t`Stock`,
      sortable: true,

      render: (record) => {
        let extra: ReactNode[] = [];

        let stock = record?.total_in_stock ?? 0;
        let allocated =
          (record?.allocated_to_build_orders ?? 0) +
          (record?.allocated_to_sales_orders ?? 0);
        let available = Math.max(0, stock - allocated);
        let min_stock = record?.minimum_stock ?? 0;

        let text = String(stock);

        let color: string | undefined = undefined;

        if (min_stock > stock) {
          extra.push(
            <Text key="min-stock" color="orange">
              {t`Minimum stock` + `: ${min_stock}`}
            </Text>
          );

          color = 'orange';
        }

        if (record.ordering > 0) {
          extra.push(
            <Text key="on-order">{t`On Order` + `: ${record.ordering}`}</Text>
          );
        }

        if (record.building) {
          extra.push(
            <Text key="building">{t`Building` + `: ${record.building}`}</Text>
          );
        }

        if (record.allocated_to_build_orders > 0) {
          extra.push(
            <Text key="bo-allocations">
              {t`Build Order Allocations` +
                `: ${record.allocated_to_build_orders}`}
            </Text>
          );
        }

        if (record.allocated_to_sales_orders > 0) {
          extra.push(
            <Text key="so-allocations">
              {t`Sales Order Allocations` +
                `: ${record.allocated_to_sales_orders}`}
            </Text>
          );
        }

        if (available != stock) {
          extra.push(
            <Text key="available">{t`Available` + `: ${available}`}</Text>
          );
        }

        // TODO: Add extra information on stock "demand"

        if (stock <= 0) {
          color = 'red';
          text = t`No stock`;
        } else if (available <= 0) {
          color = 'orange';
        } else if (available < min_stock) {
          color = 'yellow';
        }

        return (
          <TableHoverCard
            value={
              <Group spacing="xs" position="left" noWrap>
                <Text color={color}>{text}</Text>
                {record.units && (
                  <Text size="xs" color={color}>
                    [{record.units}]
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
    {
      accessor: 'price_range',
      title: t`Price Range`,
      sortable: false,
      render: (record: any) =>
        formatPriceRange(record.pricing_min, record.pricing_max)
    },
    LinkColumn()
  ];
}

/**
 * Construct a set of filters for the part table
 */
function partTableFilters(): TableFilter[] {
  return [
    {
      name: 'active',
      label: t`Active`,
      description: t`Filter by part active status`,
      type: 'boolean'
    },
    {
      name: 'assembly',
      label: t`Assembly`,
      description: t`Filter by assembly attribute`,
      type: 'boolean'
    },
    {
      name: 'cascade',
      label: t`Include Subcategories`,
      description: t`Include parts in subcategories`,
      type: 'boolean'
    },
    {
      name: 'component',
      label: t`Component`,
      description: t`Filter by component attribute`,
      type: 'boolean'
    },
    {
      name: 'trackable',
      label: t`Trackable`,
      description: t`Filter by trackable attribute`,
      type: 'boolean'
    },
    {
      name: 'has_units',
      label: t`Has Units`,
      description: t`Filter by parts which have units`,
      type: 'boolean'
    },
    {
      name: 'has_ipn',
      label: t`Has IPN`,
      description: t`Filter by parts which have an internal part number`,
      type: 'boolean'
    },
    {
      name: 'has_stock',
      label: t`Has Stock`,
      description: t`Filter by parts which have stock`,
      type: 'boolean'
    },
    {
      name: 'low_stock',
      label: t`Low Stock`,
      description: t`Filter by parts which have low stock`,
      type: 'boolean'
    },
    {
      name: 'purchaseable',
      label: t`Purchaseable`,
      description: t`Filter by parts which are purchaseable`,
      type: 'boolean'
    },
    {
      name: 'salable',
      label: t`Salable`,
      description: t`Filter by parts which are salable`,
      type: 'boolean'
    },
    {
      name: 'virtual',
      label: t`Virtual`,
      description: t`Filter by parts which are virtual`,
      type: 'choice',
      choices: [
        { value: 'true', label: t`Virtual` },
        { value: 'false', label: t`Not Virtual` }
      ]
    }
    // unallocated_stock
    // starred
    // stocktake
    // is_template
    // virtual
    // has_pricing
    // TODO: Any others from table_filters.js?
  ];
}

/**
 * PartListTable - Displays a list of parts, based on the provided parameters
 * @param {Object} params - The query parameters to pass to the API
 * @returns
 */
export function PartListTable({ props }: { props: InvenTreeTableProps }) {
  const tableColumns = useMemo(() => partTableColumns(), []);
  const tableFilters = useMemo(() => partTableFilters(), []);

  const table = useTable('part-list');

  const navigate = useNavigate();

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.part_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        ...props,
        enableDownload: true,
        customFilters: tableFilters,
        params: {
          ...props.params,
          category_detail: true
        },
        onRowClick: (record, _index, _event) => {
          navigate(`/part/${record.pk}/`);
        }
      }}
    />
  );
}
