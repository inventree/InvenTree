import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { ReactNode, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { formatCurrency, renderDate } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useStockFields } from '../../forms/StockForms';
import { getDetailUrl } from '../../functions/urls';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import {
  DescriptionColumn,
  PartColumn,
  StatusColumn
} from '../ColumnRenderers';
import { StatusFilterOptions, TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

/**
 * Construct a list of columns for the stock item table
 */
function stockItemTableColumns(): TableColumn[] {
  return [
    {
      accessor: 'part',
      sortable: true,
      render: (record: any) => PartColumn(record?.part_detail)
    },
    DescriptionColumn({
      accessor: 'part_detail.description'
    }),
    {
      accessor: 'quantity',
      ordering: 'stock',
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
      sortable: true
    },
    {
      accessor: 'location',
      sortable: true,
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
      switchable: true,
      render: (record: any) => renderDate(record.expiry_date)
    },
    {
      accessor: 'updated',
      sortable: true,
      switchable: true,
      render: (record: any) => renderDate(record.updated)
    },
    // TODO: purchase order
    // TODO: Supplier part
    {
      accessor: 'purchase_price',
      sortable: true,
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
      name: 'active',
      label: t`Active`,
      description: t`Show stock for active parts`
    },
    {
      name: 'status',
      label: t`Status`,
      description: t`Filter by stock status`,
      choiceFunction: StatusFilterOptions(ModelType.stockitem)
    },
    {
      name: 'assembly',
      label: t`Assembly`,
      description: t`Show stock for assmebled parts`
    },
    {
      name: 'allocated',
      label: t`Allocated`,
      description: t`Show items which have been allocated`
    },
    {
      name: 'available',
      label: t`Available`,
      description: t`Show items which are available`
    },
    {
      name: 'cascade',
      label: t`Include Sublocations`,
      description: t`Include stock in sublocations`
    },
    {
      name: 'depleted',
      label: t`Depleted`,
      description: t`Show depleted stock items`
    },
    {
      name: 'in_stock',
      label: t`In Stock`,
      description: t`Show items which are in stock`
    },
    {
      name: 'is_building',
      label: t`In Production`,
      description: t`Show items which are in production`
    },
    {
      name: 'include_variants',
      label: t`Include Variants`,
      description: t`Include stock items for variant parts`
    },
    {
      name: 'installed',
      label: t`Installed`,
      description: t`Show stock items which are installed in other items`
    },
    {
      name: 'sent_to_customer',
      label: t`Sent to Customer`,
      description: t`Show items which have been sent to a customer`
    },
    {
      name: 'serialized',
      label: t`Is Serialized`,
      description: t`Show items which have a serial number`
    },
    // TODO: serial
    // TODO: serial_gte
    // TODO: serial_lte
    {
      name: 'has_batch',
      label: t`Has Batch Code`,
      description: t`Show items which have a batch code`
    },
    // TODO: batch
    {
      name: 'tracked',
      label: t`Tracked`,
      description: t`Show tracked items`
    },
    {
      name: 'has_purchase_price',
      label: t`Has Purchase Price`,
      description: t`Show items which have a purchase price`
    },
    // TODO: Expired
    // TODO: stale
    // TODO: expiry_date_lte
    // TODO: expiry_date_gte
    {
      name: 'external',
      label: t`External Location`,
      description: t`Show items in an external location`
    }
  ];
}

/*
 * Load a table of stock items
 */
export function StockItemTable({ params = {} }: { params?: any }) {
  let tableColumns = useMemo(() => stockItemTableColumns(), []);
  let tableFilters = useMemo(() => stockItemTableFilters(), []);

  const table = useTable('stockitems');
  const user = useUserState();
  const navigate = useNavigate();

  const stockItemFields = useStockFields({ create: true });

  const newStockItem = useCreateApiFormModal({
    url: ApiEndpoints.stock_item_list,
    title: t`Add Stock Item`,
    fields: stockItemFields,
    initialData: {
      part: params.part,
      location: params.location
    },
    onFormSuccess: (data: any) => {
      if (data.pk) {
        navigate(getDetailUrl(ModelType.stockitem, data.pk));
      }
    }
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        hidden={!user.hasAddRole(UserRoles.stock)}
        tooltip={t`Add Stock Item`}
        onClick={() => newStockItem.open()}
      />
    ];
  }, [user]);

  return (
    <>
      {newStockItem.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.stock_item_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableDownload: true,
          enableSelection: false,
          tableFilters: tableFilters,
          tableActions: tableActions,
          onRowClick: (record) =>
            navigate(getDetailUrl(ModelType.stockitem, record.pk)),
          params: {
            ...params,
            part_detail: true,
            location_detail: true,
            supplier_part_detail: true
          }
        }}
      />
    </>
  );
}
