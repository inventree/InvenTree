import { t } from '@lingui/macro';
import { Accordion, Alert, Grid, Skeleton, Stack } from '@mantine/core';
import {
  IconBookmark,
  IconBoxPadding,
  IconChecklist,
  IconHistory,
  IconInfoCircle,
  IconPackages,
  IconShoppingCart,
  IconSitemap
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

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
import { formatCurrency } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import {
  type StockOperationProps,
  useAddStockItem,
  useAssignStockItem,
  useCountStockItem,
  useRemoveStockItem,
  useStockFields,
  useStockItemSerializeFields,
  useTransferStockItem
} from '../../forms/StockForms';
import { InvenTreeIcon } from '../../functions/icons';
import { getDetailUrl } from '../../functions/urls';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { apiUrl } from '../../states/ApiState';
import { useGlobalSettingsState } from '../../states/SettingsState';
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
    instanceQuery,
    requestStatus
  } = useInstance({
    endpoint: ApiEndpoints.stock_item_list,
    pk: id,
    params: {
      part_detail: true,
      location_detail: true,
      path_detail: true
    }
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
        type: 'text',
        name: 'tests',
        label: t`Completed Tests`,
        icon: 'progress',
        hidden: !part?.testable
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

    // Top right - available stock information
    const tr: DetailsField[] = [
      {
        type: 'text',
        name: 'quantity',
        label: t`Quantity`
      },
      {
        type: 'text',
        name: 'serial',
        label: t`Serial Number`,
        hidden: !stockitem.serial
      },
      {
        type: 'text',
        name: 'available_stock',
        label: t`Available`,
        icon: 'stock'
      },
      {
        type: 'text',
        name: 'allocated',
        label: t`Allocated to Orders`,
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
  }, [stockitem, instanceQuery.isFetching, enableExpiry]);

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
        })
        .catch(() => {
          return null;
        });
    }
  });

  const showInstalledItems: boolean = useMemo(() => {
    if (stockitem?.installed_items) {
      // There are installed items in this stock item
      return true;
    }

    if (trackedBomItemQuery.data != null) {
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
        name: 'testdata',
        label: t`Test Data`,
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
        model_id: stockitem.pk
      })
    ];
  }, [
    showSalesAllocations,
    showBuildAllocations,
    showInstalledItems,
    stockitem,
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
    partId: stockitem.part
  });

  const editStockItem = useEditApiFormModal({
    url: ApiEndpoints.stock_item_list,
    pk: stockitem.pk,
    title: t`Edit Stock Item`,
    fields: editStockItemFields,
    onFormSuccess: refreshInstance
  });

  const duplicateStockItemFields = useStockFields({ create: true });

  const duplicateStockItem = useCreateApiFormModal({
    url: ApiEndpoints.stock_item_list,
    title: t`Add Stock Item`,
    fields: duplicateStockItemFields,
    initialData: {
      ...stockitem
    },
    follow: true,
    modelType: ModelType.stockitem
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

  const stockActionProps: StockOperationProps = useMemo(() => {
    return {
      items: [stockitem],
      model: ModelType.stockitem,
      refresh: refreshInstance,
      filters: {
        in_stock: true
      }
    };
  }, [stockitem]);

  const countStockItem = useCountStockItem(stockActionProps);
  const addStockItem = useAddStockItem(stockActionProps);
  const removeStockItem = useRemoveStockItem(stockActionProps);
  const transferStockItem = useTransferStockItem(stockActionProps);
  const assignToCustomer = useAssignStockItem(stockActionProps);

  const serializeStockFields = useStockItemSerializeFields({
    partId: stockitem.part,
    trackable: stockitem.part_detail?.trackable
  });

  const serializeStockItem = useCreateApiFormModal({
    url: ApiEndpoints.stock_serialize,
    pk: stockitem.pk,
    title: t`Serialize Stock Item`,
    fields: serializeStockFields,
    initialData: {
      quantity: stockitem.quantity,
      destination: stockitem.location ?? stockitem.part_detail?.default_location
    },
    onFormSuccess: () => {
      const partId = stockitem.part;
      refreshInstancePromise().catch(() => {
        // Part may have been deleted - redirect to the part detail page
        navigate(getDetailUrl(ModelType.part, partId));
      });
    },
    successMessage: t`Stock item serialized`
  });

  const returnStockItem = useCreateApiFormModal({
    url: ApiEndpoints.stock_return,
    pk: stockitem.pk,
    title: t`Return Stock Item`,
    preFormContent: (
      <Alert color='blue'>
        {t`Return this item into stock. This will remove the customer assignment.`}
      </Alert>
    ),
    fields: {
      location: {},
      status: {},
      notes: {}
    },
    initialData: {
      location: stockitem.location ?? stockitem.part_detail?.default_location,
      status: stockitem.status_custom_key ?? stockitem.status
    },
    successMessage: t`Item returned to stock`,
    onFormSuccess: () => {
      refreshInstance();
    }
  });

  const orderPartsWizard = OrderPartsWizard({
    parts: stockitem.part_detail ? [stockitem.part_detail] : []
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
          {
            name: t`Count`,
            tooltip: t`Count stock`,
            hidden: serialized || !canTransfer || isBuilding,
            icon: (
              <InvenTreeIcon icon='stocktake' iconProps={{ color: 'blue' }} />
            ),
            onClick: () => {
              stockitem.pk && countStockItem.open();
            }
          },
          {
            name: t`Add`,
            tooltip: t`Add Stock`,
            hidden: serialized || !canTransfer || isBuilding,
            icon: <InvenTreeIcon icon='add' iconProps={{ color: 'green' }} />,
            onClick: () => {
              stockitem.pk && addStockItem.open();
            }
          },
          {
            name: t`Remove`,
            tooltip: t`Remove Stock`,
            hidden:
              serialized ||
              !canTransfer ||
              isBuilding ||
              stockitem.quantity <= 0,
            icon: <InvenTreeIcon icon='remove' iconProps={{ color: 'red' }} />,
            onClick: () => {
              stockitem.pk && removeStockItem.open();
            }
          },
          {
            name: t`Transfer`,
            tooltip: t`Transfer Stock`,
            hidden: !canTransfer,
            icon: (
              <InvenTreeIcon icon='transfer' iconProps={{ color: 'blue' }} />
            ),
            onClick: () => {
              stockitem.pk && transferStockItem.open();
            }
          },
          {
            name: t`Serialize`,
            tooltip: t`Serialize stock`,
            hidden:
              !canTransfer ||
              isBuilding ||
              serialized ||
              stockitem?.quantity != 1 ||
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
          },
          {
            name: t`Return`,
            tooltip: t`Return from customer`,
            hidden: !stockitem.customer,
            icon: (
              <InvenTreeIcon
                icon='return_orders'
                iconProps={{ color: 'blue' }}
              />
            ),
            onClick: () => {
              stockitem.pk && returnStockItem.open();
            }
          },
          {
            name: t`Assign to Customer`,
            tooltip: t`Assign to a customer`,
            hidden: !!stockitem.customer,
            icon: (
              <InvenTreeIcon icon='customer' iconProps={{ color: 'blue' }} />
            ),
            onClick: () => {
              stockitem.pk && assignToCustomer.open();
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
  }, [id, stockitem, user]);

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
            label={`${t`Quantity`}: ${stockitem.quantity}`}
            visible={!stockitem.serial}
            key='quantity'
          />,
          <DetailsBadge
            color='yellow'
            label={`${t`Available`}: ${available}`}
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
    <InstanceDetail
      requiredRole={UserRoles.stock}
      status={requestStatus}
      loading={instanceQuery.isFetching}
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
            user.hasViewRole(UserRoles.stock_location) ? breadcrumbs : undefined
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
        {editStockItem.modal}
        {duplicateStockItem.modal}
        {deleteStockItem.modal}
        {countStockItem.modal}
        {addStockItem.modal}
        {removeStockItem.modal}
        {transferStockItem.modal}
        {serializeStockItem.modal}
        {returnStockItem.modal}
        {assignToCustomer.modal}
        {orderPartsWizard.wizard}
      </Stack>
    </InstanceDetail>
  );
}
