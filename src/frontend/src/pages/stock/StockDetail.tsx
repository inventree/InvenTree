import { t } from '@lingui/core/macro';
import {
  Accordion,
  Button,
  Grid,
  Group,
  Skeleton,
  Space,
  Stack,
  Text,
  Tooltip
} from '@mantine/core';
import {
  IconArrowLeft,
  IconArrowRight,
  IconBookmark,
  IconBoxPadding,
  IconChecklist,
  IconHistory,
  IconInfoCircle,
  IconPackages,
  IconSearch,
  IconShoppingCart,
  IconSitemap
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { ActionButton } from '@lib/components/ActionButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl, getOverviewUrl } from '@lib/functions/Navigation';
import type { StockOperationProps } from '@lib/types/Forms';
import { notifications } from '@mantine/notifications';
import { useBarcodeScanDialog } from '../../components/barcodes/BarcodeScanDialog';
import AdminButton from '../../components/buttons/AdminButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import DetailsBadge from '../../components/details/DetailsBadge';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import {
  ActionDropdown,
  BarcodeActionDropdown,
  DeleteItemAction,
  DuplicateItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import { StylishText } from '../../components/items/StylishText';
import InstanceDetail from '../../components/nav/InstanceDetail';
import NavigationTree from '../../components/nav/NavigationTree';
import { PageDetail } from '../../components/nav/PageDetail';
import AttachmentPanel from '../../components/panels/AttachmentPanel';
import NotesPanel from '../../components/panels/NotesPanel';
import type { PanelType } from '../../components/panels/Panel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import LocateItemButton from '../../components/plugins/LocateItemButton';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import OrderPartsWizard from '../../components/wizards/OrderPartsWizard';
import { useApi } from '../../contexts/ApiContext';
import { formatCurrency, formatDecimal } from '../../defaults/formatters';
import {
  useFindSerialNumberForm,
  useStockFields,
  useStockItemSerializeFields
} from '../../forms/StockForms';
import { InvenTreeIcon } from '../../functions/icons';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useStockAdjustActions } from '../../hooks/UseStockAdjustActions';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import BuildAllocatedStockTable from '../../tables/build/BuildAllocatedStockTable';
import SalesOrderAllocationTable from '../../tables/sales/SalesOrderAllocationTable';
import InstalledItemsTable from '../../tables/stock/InstalledItemsTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';
import StockItemTestResultTable from '../../tables/stock/StockItemTestResultTable';
import { StockTrackingTable } from '../../tables/stock/StockTrackingTable';

export default function StockDetail() {
  const { id } = useParams();

  const api = useApi();
  const user = useUserState();

  const globalSettings = useGlobalSettingsState();

  const enableExpiry = useMemo(
    () => globalSettings.isSet('STOCK_ENABLE_EXPIRY'),
    [globalSettings]
  );

  const navigate = useNavigate();

  const [treeOpen, setTreeOpen] = useState(false);

  const {
    instance: stockitem,
    refreshInstance,
    refreshInstancePromise,
    instanceQuery
  } = useInstance({
    endpoint: ApiEndpoints.stock_item_list,
    pk: id,
    params: {
      part_detail: true,
      location_detail: true,
      path_detail: true
    }
  });

  const { instance: serialNumbers, instanceQuery: serialNumbersQuery } =
    useInstance({
      endpoint: ApiEndpoints.stock_serial_info,
      pk: id
    });

  const findBySerialNumber = useFindSerialNumberForm({
    partId: stockitem.part
  });

  const detailsPanel = useMemo(() => {
    const data = { ...stockitem };
    const part = stockitem?.part_detail ?? {};

    data.available_stock = Math.max(0, data.quantity - data.allocated);

    if (instanceQuery.isFetching) {
      return <Skeleton />;
    }

    // Top left - core part information
    const tl: DetailsField[] = [
      {
        name: 'part',
        label: t`Base Part`,
        type: 'link',
        model: ModelType.part
      },
      {
        name: 'part_detail.IPN',
        label: t`IPN`,
        type: 'text',
        copy: true,
        icon: 'part',
        hidden: !part.IPN
      },
      {
        name: 'part_detail.revision',
        label: t`Revision`,
        type: 'string',
        copy: true,
        icon: 'revision',
        hidden: !part.revision
      },
      {
        name: 'status',
        type: 'status',
        label: t`Status`,
        model: ModelType.stockitem
      },
      {
        name: 'status_custom_key',
        type: 'status',
        label: t`Custom Status`,
        model: ModelType.stockitem,
        icon: 'status',
        hidden:
          !stockitem.status_custom_key ||
          stockitem.status_custom_key == stockitem.status
      },
      {
        type: 'link',
        name: 'link',
        label: t`Link`,
        external: true,
        copy: true,
        hidden: !stockitem.link
      }
    ];

    // Top right - available stock information
    const tr: DetailsField[] = [
      {
        type: 'text',
        name: 'serial',
        label: t`Serial Number`,
        hidden: !stockitem.serial,
        value_formatter: () => (
          <Group gap='xs' justify='space-apart'>
            <Text>{stockitem.serial}</Text>
            <Space flex={10} />
            <Group gap={2} justify='right'>
              {serialNumbers.previous?.pk && (
                <Tooltip label={t`Previous serial number`} position='top'>
                  <Button
                    p={3}
                    aria-label='previous-serial-number'
                    leftSection={<IconArrowLeft />}
                    variant='transparent'
                    size='sm'
                    onClick={() => {
                      navigate(
                        getDetailUrl(
                          ModelType.stockitem,
                          serialNumbers.previous.pk
                        )
                      );
                    }}
                  >
                    {serialNumbers.previous.serial}
                  </Button>
                </Tooltip>
              )}
              <ActionButton
                icon={<IconSearch size={18} />}
                tooltip={t`Find serial number`}
                tooltipAlignment='top'
                variant='transparent'
                onClick={findBySerialNumber.open}
              />
              {serialNumbers.next?.pk && (
                <Tooltip label={t`Next serial number`} position='top'>
                  <Button
                    p={3}
                    aria-label='next-serial-number'
                    rightSection={<IconArrowRight />}
                    variant='transparent'
                    size='sm'
                    onClick={() => {
                      navigate(
                        getDetailUrl(ModelType.stockitem, serialNumbers.next.pk)
                      );
                    }}
                  >
                    {serialNumbers.next.serial}
                  </Button>
                </Tooltip>
              )}
            </Group>
          </Group>
        )
      },
      {
        type: 'number',
        name: 'quantity',
        label: t`Quantity`,
        unit: part?.units,
        hidden: !!stockitem.serial && stockitem.quantity == 1
      },
      {
        type: 'number',
        name: 'available_stock',
        label: t`Available`,
        unit: part?.units,
        icon: 'stock'
      },
      {
        type: 'number',
        name: 'allocated',
        label: t`Allocated to Orders`,
        unit: part?.units,
        icon: 'tick_off',
        hidden: !stockitem.allocated
      },
      {
        type: 'text',
        name: 'batch',
        label: t`Batch Code`,
        hidden: !stockitem.batch
      }
    ];

    // Bottom left: location information
    const bl: DetailsField[] = [
      {
        name: 'supplier_part',
        label: t`Supplier Part`,
        type: 'link',
        model_field: 'SKU',
        model: ModelType.supplierpart,
        hidden: !stockitem.supplier_part
      },
      {
        type: 'link',
        name: 'location',
        label: t`Location`,
        model: ModelType.stocklocation,
        hidden: !stockitem.location
      },
      {
        type: 'link',
        name: 'belongs_to',
        label: t`Installed In`,
        model_filters: {
          part_detail: true
        },
        model_formatter: (model: any) => {
          let text = model?.part_detail?.full_name ?? model?.name;
          if (model.serial && model.quantity == 1) {
            text += ` # ${model.serial}`;
          }

          return text;
        },
        icon: 'stock',
        model: ModelType.stockitem,
        hidden: !stockitem.belongs_to
      },
      {
        type: 'link',
        name: 'parent',
        icon: 'sitemap',
        label: t`Parent Item`,
        model: ModelType.stockitem,
        hidden: !stockitem.parent,
        model_formatter: (model: any) => {
          return t`Parent stock item`;
        }
      },
      {
        type: 'link',
        name: 'consumed_by',
        label: t`Consumed By`,
        model: ModelType.build,
        hidden: !stockitem.consumed_by,
        icon: 'build',
        model_field: 'reference'
      },
      {
        type: 'link',
        name: 'build',
        label: t`Build Order`,
        model: ModelType.build,
        hidden: !stockitem.build,
        model_field: 'reference'
      },
      {
        type: 'link',
        name: 'purchase_order',
        label: t`Purchase Order`,
        model: ModelType.purchaseorder,
        hidden: !stockitem.purchase_order,
        icon: 'purchase_orders',
        model_field: 'reference'
      },
      {
        type: 'link',
        name: 'sales_order',
        label: t`Sales Order`,
        model: ModelType.salesorder,
        hidden: !stockitem.sales_order,
        icon: 'sales_orders',
        model_field: 'reference'
      },
      {
        type: 'link',
        name: 'customer',
        label: t`Customer`,
        model: ModelType.company,
        hidden: !stockitem.customer
      }
    ];

    // Bottom right - any other information
    const br: DetailsField[] = [
      // Expiry date
      {
        type: 'date',
        name: 'expiry_date',
        label: t`Expiry Date`,
        hidden: !enableExpiry || !stockitem.expiry_date,
        icon: 'calendar'
      },
      // TODO: Ownership
      {
        type: 'text',
        name: 'purchase_price',
        label: t`Unit Price`,
        icon: 'currency',
        hidden: !stockitem.purchase_price,
        value_formatter: () => {
          return formatCurrency(stockitem.purchase_price, {
            currency: stockitem.purchase_price_currency
          });
        }
      },
      {
        type: 'text',
        name: 'stock_value',
        label: t`Stock Value`,
        icon: 'currency',
        hidden:
          !stockitem.purchase_price ||
          stockitem.quantity == 1 ||
          stockitem.quantity == 0,
        value_formatter: () => {
          return formatCurrency(stockitem.purchase_price, {
            currency: stockitem.purchase_price_currency,
            multiplier: stockitem.quantity
          });
        }
      },
      {
        type: 'text',
        name: 'packaging',
        icon: 'part',
        label: t`Packaging`,
        hidden: !stockitem.packaging
      },
      {
        type: 'text',
        name: 'updated',
        icon: 'calendar',
        label: t`Last Updated`
      },
      {
        type: 'text',
        name: 'stocktake',
        icon: 'calendar',
        label: t`Last Stocktake`,
        hidden: !stockitem.stocktake
      }
    ];

    return (
      <ItemDetailsGrid>
        <Grid grow>
          <DetailsImage
            appRole={UserRoles.part}
            apiPath={ApiEndpoints.part_list}
            src={
              stockitem.part_detail?.image ?? stockitem?.part_detail?.thumbnail
            }
            pk={stockitem.part}
          />
          <Grid.Col span={{ base: 12, sm: 8 }}>
            <DetailsTable fields={tl} item={data} />
          </Grid.Col>
        </Grid>
        <DetailsTable fields={tr} item={data} />
        <DetailsTable fields={bl} item={data} />
        <DetailsTable fields={br} item={data} />
      </ItemDetailsGrid>
    );
  }, [
    stockitem,
    serialNumbers,
    serialNumbersQuery.isFetching,
    instanceQuery.isFetching,
    enableExpiry
  ]);

  const showBuildAllocations: boolean = useMemo(() => {
    // Determine if "build allocations" should be shown for this stock item
    return (
      stockitem?.part_detail?.component && // Must be a "component"
      !stockitem?.sales_order && // Must not be assigned to a sales order
      !stockitem?.belongs_to
    ); // Must not be installed into another item
  }, [stockitem]);

  const showSalesAllocations: boolean = useMemo(() => {
    return stockitem?.part_detail?.salable;
  }, [stockitem]);

  // API query to determine if this stock item has trackable BOM items
  const trackedBomItemQuery = useQuery({
    queryKey: ['tracked-bom-item', stockitem.pk, stockitem.part],
    queryFn: () => {
      if (
        !stockitem.pk ||
        !stockitem.part ||
        !stockitem.part_detail?.assembly
      ) {
        return false;
      }

      return api
        .get(apiUrl(ApiEndpoints.bom_list), {
          params: {
            part: stockitem.part,
            sub_part_trackable: true,
            limit: 1
          }
        })
        .then((response) => {
          if (response.status == 200) {
            return response.data.count > 0;
          } else {
            return null;
          }
        });
    }
  });

  const showInstalledItems: boolean = useMemo(() => {
    if (stockitem?.installed_items) {
      // There are installed items in this stock item
      return true;
    }

    if (!!trackedBomItemQuery.data) {
      return trackedBomItemQuery.data;
    }

    // Fall back to whether this is an assembly or not
    return stockitem?.part_detail?.assembly;
  }, [trackedBomItemQuery, stockitem]);

  const stockPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Stock Details`,
        icon: <IconInfoCircle />,
        content: detailsPanel
      },
      {
        name: 'tracking',
        label: t`Stock Tracking`,
        icon: <IconHistory />,
        content: stockitem.pk ? (
          <StockTrackingTable itemId={stockitem.pk} />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'allocations',
        label: t`Allocations`,
        icon: <IconBookmark />,
        hidden:
          !stockitem.in_stock ||
          (!showSalesAllocations && !showBuildAllocations),
        content: (
          <Accordion
            multiple={true}
            defaultValue={['buildAllocations', 'salesAllocations']}
          >
            {showBuildAllocations && (
              <Accordion.Item value='buildAllocations' key='buildAllocations'>
                <Accordion.Control>
                  <StylishText size='lg'>{t`Build Order Allocations`}</StylishText>
                </Accordion.Control>
                <Accordion.Panel>
                  <BuildAllocatedStockTable
                    stockId={stockitem.pk}
                    modelField='build'
                    modelTarget={ModelType.build}
                    showBuildInfo
                  />
                </Accordion.Panel>
              </Accordion.Item>
            )}
            {showSalesAllocations && (
              <Accordion.Item value='salesAllocations' key='salesAllocations'>
                <Accordion.Control>
                  <StylishText size='lg'>{t`Sales Order Allocations`}</StylishText>
                </Accordion.Control>
                <Accordion.Panel>
                  <SalesOrderAllocationTable
                    stockId={stockitem.pk}
                    modelField='order'
                    modelTarget={ModelType.salesorder}
                    showOrderInfo
                  />
                </Accordion.Panel>
              </Accordion.Item>
            )}
          </Accordion>
        )
      },
      {
        name: 'test-results',
        label: t`Test Results`,
        icon: <IconChecklist />,
        hidden: !stockitem?.part_detail?.testable,
        content: stockitem?.pk ? (
          <StockItemTestResultTable
            itemId={stockitem.pk}
            partId={stockitem.part}
          />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'installed_items',
        label: t`Installed Items`,
        icon: <IconBoxPadding />,
        hidden: !showInstalledItems,
        content: <InstalledItemsTable stockItem={stockitem} />
      },
      {
        name: 'child_items',
        label: t`Child Items`,
        icon: <IconSitemap />,
        hidden: (stockitem?.child_items ?? 0) == 0,
        content: stockitem?.pk ? (
          <StockItemTable
            tableName='child-stock'
            params={{ ancestor: stockitem.pk }}
          />
        ) : (
          <Skeleton />
        )
      },
      AttachmentPanel({
        model_type: ModelType.stockitem,
        model_id: stockitem.pk
      }),
      NotesPanel({
        model_type: ModelType.stockitem,
        model_id: stockitem.pk,
        has_note: !!stockitem.notes
      })
    ];
  }, [
    showSalesAllocations,
    showBuildAllocations,
    showInstalledItems,
    stockitem,
    serialNumbers,
    serialNumbersQuery,
    id,
    user
  ]);

  const breadcrumbs = useMemo(
    () => [
      { name: t`Stock`, url: '/stock' },
      ...(stockitem.location_path ?? []).map((l: any) => ({
        name: l.name,
        url: getDetailUrl(ModelType.stocklocation, l.pk)
      }))
    ],
    [stockitem]
  );

  const editStockItemFields = useStockFields({
    create: false,
    stockItem: stockitem,
    partId: stockitem.part,
    modalId: 'edit-stock-item'
  });

  const editStockItem = useEditApiFormModal({
    url: ApiEndpoints.stock_item_list,
    pk: stockitem.pk,
    title: t`Edit Stock Item`,
    modalId: 'edit-stock-item',
    fields: editStockItemFields,
    onFormSuccess: refreshInstance
  });

  const duplicateStockItemFields = useStockFields({
    create: true,
    modalId: 'duplicate-stock-item'
  });

  const duplicateStockData = useMemo(() => {
    const duplicate = {
      ...stockitem,
      serial_numbers: stockitem.serial
    };

    // Omit the "serial" field for item creation
    delete duplicate.serial;

    return duplicate;
  }, [stockitem]);

  const duplicateStockItem = useCreateApiFormModal({
    url: ApiEndpoints.stock_item_list,
    title: t`Add Stock Item`,
    modalId: 'duplicate-stock-item',
    fields: duplicateStockItemFields,
    initialData: {
      ...duplicateStockData
    },
    follow: true,
    successMessage: null,
    modelType: ModelType.stockitem,
    onFormSuccess: (data) => {
      // Handle case where multiple stock items are created
      if (Array.isArray(data) && data.length > 0) {
        if (data.length == 1) {
          navigate(getDetailUrl(ModelType.stockitem, data[0]?.pk));
        } else {
          const n: number = data.length;
          notifications.show({
            title: t`Items Created`,
            message: t`Created ${n} stock items`,
            color: 'green'
          });
        }
      }
    }
  });

  const preDeleteContent = useMemo(() => {
    // TODO: Fill this out with information on the stock item.
    // e.g. list of child items which would be deleted, etc
    return undefined;
  }, [stockitem]);

  const deleteStockItem = useDeleteApiFormModal({
    url: ApiEndpoints.stock_item_list,
    pk: stockitem.pk,
    title: t`Delete Stock Item`,
    preFormContent: preDeleteContent,
    onFormSuccess: () => {
      // Redirect to the part page
      navigate(getDetailUrl(ModelType.part, stockitem.part));
    }
  });

  const stockOperationProps: StockOperationProps = useMemo(() => {
    return {
      items: [stockitem],
      model: ModelType.stockitem,
      refresh: () => {
        const location = stockitem?.location;
        refreshInstancePromise().then((response) => {
          if (response.status == 'error') {
            // If an error occurs refreshing the instance,
            // the stock likely has likely been depleted
            if (location) {
              navigate(getDetailUrl(ModelType.stocklocation, location));
            } else {
              navigate(getOverviewUrl(ModelType.stockitem));
            }
          }
        });
      },
      filters: {
        in_stock: true
      }
    };
  }, [stockitem]);

  const stockAdjustActions = useStockAdjustActions({
    formProps: stockOperationProps,
    delete: false,
    assign: !!stockitem.in_stock && stockitem.part_detail?.salable,
    return: !!stockitem.consumed_by || !!stockitem.customer,
    merge: false
  });

  const serializeStockFields = useStockItemSerializeFields({
    partId: stockitem.part,
    trackable: stockitem.part_detail?.trackable,
    modalId: 'stock-item-serialize'
  });

  const serializeStockItem = useCreateApiFormModal({
    url: ApiEndpoints.stock_serialize,
    pk: stockitem.pk,
    title: t`Serialize Stock Item`,
    modalId: 'stock-item-serialize',
    fields: serializeStockFields,
    initialData: {
      quantity: stockitem.quantity,
      destination: stockitem.location ?? stockitem.part_detail?.default_location
    },
    onFormSuccess: (response: any) => {
      if (response.length >= stockitem.quantity) {
        // Entire item was serialized
        // Navigate to the first result
        navigate(getDetailUrl(ModelType.stockitem, response[0].pk));
      } else {
        refreshInstance();
      }
    },
    successMessage: t`Stock item serialized`
  });

  const orderPartsWizard = OrderPartsWizard({
    parts: stockitem.part_detail ? [stockitem.part_detail] : []
  });

  const scanIntoLocation = useBarcodeScanDialog({
    title: t`Scan Into Location`,
    modelType: ModelType.stocklocation,
    callback: async (barcode, response) => {
      const pk = response.stocklocation.pk;

      return api
        .post(apiUrl(ApiEndpoints.stock_transfer), {
          location: pk,
          items: [
            {
              pk: stockitem.pk,
              quantity: stockitem.quantity
            }
          ]
        })
        .then(() => {
          refreshInstance();
          return {
            success: t`Scanned stock item into location`
          };
        })
        .catch((error) => {
          console.log('Error scanning stock item:', error);
          return {
            error: t`Error scanning stock item`
          };
        });
    }
  });

  const stockActions = useMemo(() => {
    // Can this stock item be transferred to a different location?
    const canTransfer =
      user.hasChangeRole(UserRoles.stock) &&
      !stockitem.sales_order &&
      !stockitem.belongs_to &&
      !stockitem.customer &&
      !stockitem.consumed_by;

    const isBuilding = stockitem.is_building;

    const serial = stockitem.serial;
    const serialized =
      serial != null &&
      serial != undefined &&
      serial != '' &&
      stockitem.quantity == 1;

    return [
      <AdminButton model={ModelType.stockitem} id={stockitem.pk} />,
      <LocateItemButton stockId={stockitem.pk} />,
      <BarcodeActionDropdown
        model={ModelType.stockitem}
        pk={stockitem.pk}
        hash={stockitem?.barcode_hash}
        perm={user.hasChangeRole(UserRoles.stock)}
        actions={[
          {
            name: t`Scan into location`,
            icon: <InvenTreeIcon icon='location' />,
            tooltip: t`Scan this item into a location`,
            onClick: scanIntoLocation.open
          }
        ]}
      />,
      <PrintingActions
        modelType={ModelType.stockitem}
        items={[stockitem.pk]}
        enableReports
        enableLabels
      />,
      <ActionDropdown
        tooltip={t`Stock Operations`}
        icon={<IconPackages />}
        actions={[
          ...stockAdjustActions.menuActions,
          {
            name: t`Serialize`,
            tooltip: t`Serialize stock`,
            hidden:
              serialized ||
              stockitem?.quantity < 1 ||
              stockitem?.part_detail?.trackable != true,
            icon: <InvenTreeIcon icon='serial' iconProps={{ color: 'blue' }} />,
            onClick: () => {
              serializeStockItem.open();
            }
          },
          {
            name: t`Order`,
            tooltip: t`Order Stock`,
            hidden:
              !user.hasAddRole(UserRoles.purchase_order) ||
              !stockitem.part_detail?.active ||
              !stockitem.part_detail?.purchaseable,
            icon: <IconShoppingCart color='blue' />,
            onClick: () => {
              orderPartsWizard.openWizard();
            }
          }
        ]}
      />,
      <OptionsActionDropdown
        tooltip={t`Stock Item Actions`}
        actions={[
          DuplicateItemAction({
            hidden: !user.hasAddRole(UserRoles.stock),
            onClick: () => duplicateStockItem.open()
          }),
          EditItemAction({
            hidden: !user.hasChangeRole(UserRoles.stock),
            onClick: () => editStockItem.open()
          }),
          DeleteItemAction({
            hidden: !user.hasDeleteRole(UserRoles.stock),
            onClick: () => deleteStockItem.open()
          })
        ]}
      />
    ];
  }, [id, stockitem, user, stockAdjustActions.menuActions]);

  const stockBadges: ReactNode[] = useMemo(() => {
    let available = (stockitem?.quantity ?? 0) - (stockitem?.allocated ?? 0);
    available = Math.max(0, available);

    return instanceQuery.isLoading
      ? []
      : [
          <DetailsBadge
            color='yellow'
            label={t`In Production`}
            visible={stockitem.is_building}
          />,
          <DetailsBadge
            color='blue'
            label={`${t`Serial Number`}: ${stockitem.serial}`}
            visible={!!stockitem.serial}
            key='serial'
          />,
          <DetailsBadge
            color='blue'
            label={`${t`Quantity`}: ${formatDecimal(stockitem.quantity)}`}
            visible={!stockitem.serial}
            key='quantity'
          />,
          <DetailsBadge
            color='yellow'
            label={`${t`Available`}: ${formatDecimal(available)}`}
            visible={
              stockitem.in_stock &&
              !stockitem.serial &&
              available != stockitem.quantity
            }
            key='available'
          />,
          <DetailsBadge
            color='blue'
            label={`${t`Batch Code`}: ${stockitem.batch}`}
            visible={!!stockitem.batch}
            key='batch'
          />,
          <StatusRenderer
            status={stockitem.status_custom_key || stockitem.status}
            fallbackStatus={stockitem.status}
            type={ModelType.stockitem}
            options={{
              size: 'lg'
            }}
            key='status'
          />,
          <DetailsBadge
            color='yellow'
            label={t`Stale`}
            visible={enableExpiry && stockitem.stale && !stockitem.expired}
            key='stale'
          />,
          <DetailsBadge
            color='orange'
            label={t`Expired`}
            visible={enableExpiry && stockitem.expired}
            key='expired'
          />,
          <DetailsBadge
            color='red'
            label={t`Unavailable`}
            visible={stockitem.in_stock == false}
            key='unavailable'
          />
        ];
  }, [stockitem, instanceQuery, enableExpiry]);

  return (
    <>
      {findBySerialNumber.modal}
      {scanIntoLocation.dialog}
      <InstanceDetail
        query={instanceQuery}
        requiredPermission={ModelType.stockitem}
      >
        <Stack>
          {user.hasViewRole(UserRoles.stock_location) && (
            <NavigationTree
              title={t`Stock Locations`}
              modelType={ModelType.stocklocation}
              endpoint={ApiEndpoints.stock_location_tree}
              opened={treeOpen}
              onClose={() => setTreeOpen(false)}
              selectedId={stockitem?.location}
            />
          )}
          <PageDetail
            title={t`Stock Item`}
            subtitle={stockitem.part_detail?.full_name}
            imageUrl={stockitem.part_detail?.thumbnail}
            editAction={editStockItem.open}
            editEnabled={user.hasChangePermission(ModelType.stockitem)}
            badges={stockBadges}
            breadcrumbs={
              user.hasViewRole(UserRoles.stock_location)
                ? breadcrumbs
                : undefined
            }
            lastCrumb={[
              {
                name: stockitem.name,
                url: `/stock/item/${stockitem.pk}/`
              }
            ]}
            breadcrumbAction={() => {
              setTreeOpen(true);
            }}
            actions={stockActions}
          />
          <PanelGroup
            pageKey='stockitem'
            panels={stockPanels}
            model={ModelType.stockitem}
            id={stockitem.pk}
            instance={stockitem}
          />
        </Stack>
      </InstanceDetail>
      {editStockItem.modal}
      {duplicateStockItem.modal}
      {deleteStockItem.modal}
      {serializeStockItem.modal}
      {stockAdjustActions.modals.map((modal) => modal.modal)}
      {orderPartsWizard.wizard}
    </>
  );
}
