import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { editPart } from '../../../functions/forms/PartForms';
import { notYetImplemented } from '../../../functions/notifications';
import { shortenString } from '../../../functions/tables';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import { TableColumn } from '../Column';
import { TableFilter } from '../Filter';
import { InvenTreeTable, InvenTreeTableProps } from '../InvenTreeTable';
import { RowAction } from '../RowActions';

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
        // TODO - Link to the part detail page
        return (
          <Group spacing="xs" align="left" noWrap={true}>
            <Thumbnail
              src={record.thumbnail || record.image}
              alt={record.name}
              size={24}
            />
            <Text>{record.full_name}</Text>
          </Group>
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
          str: record.category_detail?.pathstring
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

/**
 * PartListTable - Displays a list of parts, based on the provided parameters
 * @param {Object} params - The query parameters to pass to the API
 * @returns
 */
export function PartListTable({ props }: { props: InvenTreeTableProps }) {
  const tableColumns = useMemo(() => partTableColumns(), []);
  const tableFilters = useMemo(() => partTableFilters(), []);

  const { tableKey, refreshTable } = useTableRefresh('part');

  // Callback function for generating set of row actions
  function partTableRowActions(record: any): RowAction[] {
    let actions: RowAction[] = [];

    actions.push({
      title: t`Edit`,
      onClick: () => {
        editPart({
          part_id: record.pk,
          callback: () => {
            // TODO: Reload the table, somehow?
            notYetImplemented();
          }
        });
      }
    });

    actions.push({
      title: t`Detail`,
      onClick: () => {
        navigate(`/part/${record.pk}/`);
      }
    });

    return actions;
  }

  const navigate = useNavigate();

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.part_list)}
      tableKey={tableKey}
      columns={tableColumns}
      props={{
        ...props,
        enableDownload: true,
        customFilters: tableFilters,
        rowActions: partTableRowActions,
        params: {
          ...props.params,
          category_detail: true
        }
      }}
    />
  );
}
