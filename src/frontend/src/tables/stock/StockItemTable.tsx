import { t } from '@lingui/core/macro';
import { Group, Text } from '@mantine/core';
import { type ReactNode, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import { ActionButton } from '../../components/buttons/ActionButton';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import OrderPartsWizard from '../../components/wizards/OrderPartsWizard';
import { formatCurrency, formatPriceRange } from '../../defaults/formatters';
import {
  type StockOperationProps,
  useStockFields
} from '../../forms/StockForms';
import { InvenTreeIcon } from '../../functions/icons';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useStockAdjustActions } from '../../hooks/UseStockAdjustActions';
import { useTable } from '../../hooks/UseTable';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import {
  DateColumn,
  DescriptionColumn,
  PartColumn,
  PathColumn,
  StatusColumn
} from '../ColumnRenderers';
import {
  BatchFilter,
  HasBatchCodeFilter,
  IsSerializedFilter,
  SerialFilter,
  SerialGTEFilter,
  SerialLTEFilter,
  StatusFilterOptions
} from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

/**
 * Construct a list of columns for the stock item table
 */
function stockItemTableColumns({
  showLocation,
  showPricing
}: {
  showLocation: boolean;
  showPricing: boolean;
}): TableColumn[] {
  return [
    {
      accessor: 'part',
      sortable: true,
      render: (record: any) => PartColumn({ part: record?.part_detail })
    },
    {
      accessor: 'part_detail.IPN',
      title: t`IPN`,
      sortable: true
    },
    {
      accessor: 'part_detail.revision',
      title: t`Revision`,
      sortable: true,
      defaultVisible: false
    },
    DescriptionColumn({
      accessor: 'part_detail.description'
    }),
    {
      accessor: 'quantity',
      ordering: 'stock',
      sortable: true,
      title: t`Stock`,
      render: (record: any) => {
        // TODO: Push this out into a custom renderer
        const quantity = record?.quantity ?? 0;
        const allocated = record?.allocated ?? 0;
        const available = quantity - allocated;
        let text = quantity;
        const part = record?.part_detail ?? {};
        const extra: ReactNode[] = [];
        let color = undefined;

        if (record.serial && quantity == 1) {
          text = `# ${record.serial}`;
        }

        if (record.is_building) {
          color = 'blue';
          extra.push(
            <Text
              key='production'
              size='sm'
            >{t`This stock item is in production`}</Text>
          );
        } else if (record.sales_order) {
          extra.push(
            <Text
              key='sales-order'
              size='sm'
            >{t`This stock item has been assigned to a sales order`}</Text>
          );
        } else if (record.customer) {
          extra.push(
            <Text
              key='customer'
              size='sm'
            >{t`This stock item has been assigned to a customer`}</Text>
          );
        } else if (record.belongs_to) {
          extra.push(
            <Text
              key='belongs-to'
              size='sm'
            >{t`This stock item is installed in another stock item`}</Text>
          );
        } else if (record.consumed_by) {
          extra.push(
            <Text
              key='consumed-by'
              size='sm'
            >{t`This stock item has been consumed by a build order`}</Text>
          );
        } else if (!record.in_stock) {
          extra.push(
            <Text
              key='unavailable'
              size='sm'
            >{t`This stock item is unavailable`}</Text>
          );
        }

        if (record.expired) {
          extra.push(
            <Text
              key='expired'
              size='sm'
            >{t`This stock item has expired`}</Text>
          );
        } else if (record.stale) {
          extra.push(
            <Text key='stale' size='sm'>{t`This stock item is stale`}</Text>
          );
        }

        if (record.in_stock) {
          if (allocated > 0) {
            if (allocated >= quantity) {
              color = 'orange';
              extra.push(
                <Text
                  key='fully-allocated'
                  size='sm'
                >{t`This stock item is fully allocated`}</Text>
              );
            } else {
              extra.push(
                <Text
                  key='partially-allocated'
                  size='sm'
                >{t`This stock item is partially allocated`}</Text>
              );
            }
          }

          if (available != quantity) {
            if (available > 0) {
              extra.push(
                <Text key='available' size='sm' c='orange'>
                  {`${t`Available`}: ${available}`}
                </Text>
              );
            } else {
              extra.push(
                <Text
                  key='no-stock'
                  size='sm'
                  c='red'
                >{t`No stock available`}</Text>
              );
            }
          }

          if (quantity <= 0) {
            extra.push(
              <Text
                key='depleted'
                size='sm'
              >{t`This stock item has been depleted`}</Text>
            );
          }
        }

        if (!record.in_stock) {
          color = 'red';
        }

        return (
          <TableHoverCard
            value={
              <Group gap='xs' justify='left' wrap='nowrap'>
                <Text c={color}>{text}</Text>
                {part.units && (
                  <Text size='xs' c={color}>
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
    StatusColumn({ model: ModelType.stockitem }),
    {
      accessor: 'batch',
      sortable: true
    },
    PathColumn({
      accessor: 'location_detail',
      title: t`Location`,
      hidden: !showLocation
    }),
    {
      accessor: 'purchase_order',
      title: t`Purchase Order`,
      defaultVisible: false,
      render: (record: any) => {
        return record.purchase_order_reference;
      }
    },
    {
      accessor: 'SKU',
      title: t`Supplier Part`,
      sortable: true,
      defaultVisible: false
    },
    {
      accessor: 'MPN',
      title: t`Manufacturer Part`,
      sortable: true,
      defaultVisible: false
    },
    {
      accessor: 'purchase_price',
      title: t`Unit Price`,
      sortable: true,
      switchable: true,
      hidden: !showPricing,
      defaultVisible: false,
      render: (record: any) =>
        formatCurrency(record.purchase_price, {
          currency: record.purchase_price_currency
        })
    },
    {
      accessor: 'stock_value',
      title: t`Stock Value`,
      sortable: false,
      hidden: !showPricing,
      render: (record: any) => {
        const min_price =
          record.purchase_price || record.part_detail?.pricing_min;
        const max_price =
          record.purchase_price || record.part_detail?.pricing_max;
        const currency = record.purchase_price_currency || undefined;

        return formatPriceRange(min_price, max_price, {
          currency: currency,
          multiplier: record.quantity
        });
      }
    },
    {
      accessor: 'packaging',
      sortable: true,
      defaultVisible: false
    },

    DateColumn({
      title: t`Expiry Date`,
      accessor: 'expiry_date',
      hidden: !useGlobalSettingsState.getState().isSet('STOCK_ENABLE_EXPIRY'),
      defaultVisible: false
    }),
    DateColumn({
      title: t`Last Updated`,
      accessor: 'updated'
    }),
    DateColumn({
      accessor: 'stocktake_date',
      title: t`Stocktake Date`,
      sortable: true
    })
  ];
}

/**
 * Construct a list of available filters for the stock item table
 */
function stockItemTableFilters({
  enableExpiry
}: {
  enableExpiry: boolean;
}): TableFilter[] {
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
      description: t`Show stock for assembled parts`
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
      name: 'consumed',
      label: t`Consumed`,
      description: t`Show items which have been consumed by a build order`
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
    HasBatchCodeFilter(),
    BatchFilter(),
    IsSerializedFilter(),
    SerialFilter(),
    SerialLTEFilter(),
    SerialGTEFilter(),
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
    {
      name: 'expired',
      label: t`Expired`,
      description: t`Show items which have expired`,
      active: enableExpiry
    },
    {
      name: 'stale',
      label: t`Stale`,
      description: t`Show items which are stale`,
      active: enableExpiry
    },
    {
      name: 'expiry_before',
      label: t`Expired Before`,
      description: t`Show items which expired before this date`,
      type: 'date',
      active: enableExpiry
    },
    {
      name: 'expiry_after',
      label: t`Expired After`,
      description: t`Show items which expired after this date`,
      type: 'date',
      active: enableExpiry
    },
    {
      name: 'updated_before',
      label: t`Updated Before`,
      description: t`Show items updated before this date`,
      type: 'date'
    },
    {
      name: 'updated_after',
      label: t`Updated After`,
      description: t`Show items updated after this date`,
      type: 'date'
    },
    {
      name: 'stocktake_before',
      label: t`Stocktake Before`,
      description: t`Show items counted before this date`,
      type: 'date'
    },
    {
      name: 'stocktake_after',
      label: t`Stocktake After`,
      description: t`Show items counted after this date`,
      type: 'date'
    },
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
export function StockItemTable({
  params = {},
  allowAdd = false,
  showLocation = true,
  showPricing = true,
  tableName = 'stockitems'
}: Readonly<{
  params?: any;
  allowAdd?: boolean;
  showLocation?: boolean;
  showPricing?: boolean;
  tableName: string;
}>) {
  const table = useTable(tableName);
  const user = useUserState();

  const settings = useGlobalSettingsState();

  const stockExpiryEnabled = useMemo(
    () => settings.isSet('STOCK_ENABLE_EXPIRY'),
    [settings]
  );

  const tableColumns = useMemo(
    () =>
      stockItemTableColumns({
        showLocation: showLocation ?? true,
        showPricing: showPricing ?? true
      }),
    [showLocation, showPricing]
  );

  const tableFilters = useMemo(
    () =>
      stockItemTableFilters({
        enableExpiry: stockExpiryEnabled
      }),
    [stockExpiryEnabled]
  );

  const stockOperationProps: StockOperationProps = useMemo(() => {
    return {
      items: table.selectedRecords,
      model: ModelType.stockitem,
      refresh: table.refreshTable,
      filters: {
        in_stock: true
      }
    };
  }, [table.selectedRecords, table.refreshTable]);

  const newStockItemFields = useStockFields({
    create: true,
    partId: params.part,
    modalId: 'add-stock-item'
  });

  const newStockItem = useCreateApiFormModal({
    url: ApiEndpoints.stock_item_list,
    title: t`Add Stock Item`,
    modalId: 'add-stock-item',
    fields: newStockItemFields,
    initialData: {
      part: params.part,
      location: params.location
    },
    follow: true,
    table: table,
    modelType: ModelType.stockitem
  });

  const [partsToOrder, setPartsToOrder] = useState<any[]>([]);

  const orderPartsWizard = OrderPartsWizard({
    parts: partsToOrder
  });

  const stockAdjustActions = useStockAdjustActions({
    formProps: stockOperationProps
  });

  const tableActions = useMemo(() => {
    return [
      stockAdjustActions.dropdown,
      <ActionButton
        key='stock-order'
        hidden={!user.hasAddRole(UserRoles.purchase_order)}
        tooltip={t`Order items`}
        icon={<InvenTreeIcon icon='buy' />}
        disabled={!table.hasSelectedRecords}
        onClick={() => {
          setPartsToOrder(
            table.selectedRecords.map((record) => record.part_detail)
          );
          orderPartsWizard.openWizard();
        }}
      />,
      <AddItemButton
        key='add-stock-item'
        hidden={!allowAdd || !user.hasAddRole(UserRoles.stock)}
        tooltip={t`Add Stock Item`}
        onClick={() => newStockItem.open()}
      />
    ];
  }, [
    user,
    allowAdd,
    table.hasSelectedRecords,
    table.selectedRecords,
    stockAdjustActions.dropdown
  ]);

  return (
    <>
      {newStockItem.modal}
      {orderPartsWizard.wizard}
      {stockAdjustActions.modals.map((modal) => modal.modal)}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.stock_item_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableDownload: true,
          enableSelection: true,
          enableLabels: true,
          enableReports: true,
          tableFilters: tableFilters,
          tableActions: tableActions,
          modelType: ModelType.stockitem,
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
