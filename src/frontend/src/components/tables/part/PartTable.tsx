import { t } from '@lingui/macro';

import { shortenString } from '../../../functions/tables';

import { ThumbnailHoverCard } from '../../items/Thumbnail';

import { InvenTreeTable } from '../InvenTreeTable';
import { notYetImplemented } from '../../../functions/notifications';

import { Text } from '@mantine/core';
import { TableColumn } from '../Column';
import { TableFilter } from '../Filter';


/**
 * Construct a list of columns for the part table
 */
function partTableColumns() : TableColumn[] {
  return [
    {
      accessor: 'name',
      sortable: true,
      title: t`Part`,
      render: function(record: any) {

        // TODO - Link to the part detail page
        return <ThumbnailHoverCard
          src={record.thumbnail || record.image}
          text={record.name}
          link=""
        />;
      }
    },
    {
      accessor: 'IPN',
      title: t`IPN`,
      sortable: true,
      switchable: true,
    },
    {
      accessor: 'units',
      sortable: true,
      title: t`Units`,
      switchable: true,
    },
    {
      accessor: 'description',
      title: t`Description`,
      sortable: true,
      switchable: true,
    },
    {
      accessor: 'category',
      title: t`Category`,
      sortable: true,
      render: function(record: any) {
        // TODO: Link to the category detail page
        return shortenString({
          str: record.category_detail.pathstring,
        });
      }
    },
    {
      accessor: 'total_in_stock',
      title: t`Stock`,
      sortable: true,
      switchable: true,
    },
    {
      accessor: 'price_range',
      title: t`Price Range`,
      sortable: false,
      switchable: true,
      render: function(record: any) {
        // TODO: Render price range
        return "-- price --";
      }
    },
    {
      accessor: 'link',
      title: t`Link`,
      switchable: true,
    }
  ];
}

/**
 * Construct a set of filters for the part table
 */
function partTableFilters() : TableFilter[] {
  return [
    {
      name: 'active',
      label: t`Active`,
      description: t`Filter by part active status`,
      type: 'boolean',
    },
  ];
}


/**
 * PartListTable - Displays a list of parts, based on the provided parameters
 * @param {Object} params - The query parameters to pass to the API
 * @returns 
 */
export function PartListTable({
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
        enableDownload
        tableKey='part-table'
        printingActions={[
          <Text onClick={notYetImplemented}>Hello</Text>,
          <Text onClick={notYetImplemented}>World</Text>
        ]}
        columns={partTableColumns()}
        customFilters={partTableFilters()}
    />;
}
