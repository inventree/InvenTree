import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { useMemo } from 'react';

import { notYetImplemented } from '../../../functions/notifications';
import { shortenString } from '../../../functions/tables';
import { ThumbnailHoverCard } from '../../items/Thumbnail';
import { TableColumn } from '../Column';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Construct a list of columns for the part table
 */
function partTableColumns(): TableColumn[] {
  return [
    {
      accessor: 'name',
      sortable: true,
      title: t`Part`,
      render: function (record: any) {
        // TODO - Link to the part detail page
        return (
          <ThumbnailHoverCard
            src={record.thumbnail || record.image}
            text={record.name}
            link=""
          />
        );
      }
    },
    {
      accessor: 'IPN',
      title: t`IPN`,
      sortable: true,
      switchable: true
    },
    {
      accessor: 'units',
      sortable: true,
      title: t`Units`,
      switchable: true
    },
    {
      accessor: 'description',
      title: t`Description`,
      sortable: true,
      switchable: true
    },
    {
      accessor: 'category',
      title: t`Category`,
      sortable: true,
      render: function (record: any) {
        // TODO: Link to the category detail page
        return shortenString({
          str: record.category_detail.pathstring
        });
      }
    },
    {
      accessor: 'total_in_stock',
      title: t`Stock`,
      sortable: true,
      switchable: true
    },
    {
      accessor: 'price_range',
      title: t`Price Range`,
      sortable: false,
      switchable: true,
      render: function (record: any) {
        // TODO: Render price range
        return '-- price --';
      }
    },
    {
      accessor: 'link',
      title: t`Link`,
      switchable: true
    }
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

function partTableParams(params: any): any {
  return {
    ...params,
    category_detail: true
  };
}

/**
 * PartListTable - Displays a list of parts, based on the provided parameters
 * @param {Object} params - The query parameters to pass to the API
 * @returns
 */
export function PartListTable({ params = {} }: { params?: any }) {
  let tableParams = useMemo(() => partTableParams(params), []);
  let tableColumns = useMemo(() => partTableColumns(), []);
  let tableFilters = useMemo(() => partTableFilters(), []);

  // Add required query parameters
  tableParams.category_detail = true;

  return (
    <InvenTreeTable
      url="part/"
      enableDownload
      tableKey="part-table"
      printingActions={[
        <Text onClick={notYetImplemented}>Hello</Text>,
        <Text onClick={notYetImplemented}>World</Text>
      ]}
      params={tableParams}
      columns={tableColumns}
      customFilters={tableFilters}
    />
  );
}
