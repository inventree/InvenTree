import { t } from '@lingui/core/macro';
import { Accordion, Skeleton, Stack } from '@mantine/core';
import {
  IconBookmark,
  IconBoxPadding,
  IconChecklist,
  IconHistory,
  IconInfoCircle,
  IconPackages,
  IconShoppingCart,
  IconSitemap,
  IconTransform
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl, getOverviewUrl } from '@lib/functions/Navigation';
import type { ApiFormFieldSet, StockOperationProps } from '@lib/types/Forms';
import type { PanelType } from '@lib/types/Panel';
import { notifications } from '@mantine/notifications';
import { useBarcodeScanDialog } from '../../components/barcodes/BarcodeScanDialog';
import AdminButton from '../../components/buttons/AdminButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import DetailsBadge from '../../components/details/DetailsBadge';
import {
  ActionDropdown,
  BarcodeActionDropdown,
  DeleteItemAction,
  DuplicateItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import InstanceDetail from '../../components/nav/InstanceDetail';
import NavigationTree from '../../components/nav/NavigationTree';
import { PageDetail } from '../../components/nav/PageDetail';
import AttachmentPanel from '../../components/panels/AttachmentPanel';
import NotesPanel from '../../components/panels/NotesPanel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import LocateItemButton from '../../components/plugins/LocateItemButton';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import OrderPartsWizard from '../../components/wizards/OrderPartsWizard';
import { useApi } from '../../contexts/ApiContext';
import { formatDecimal } from '../../defaults/formatters';
import {
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
import TransferOrderAllocationTable from '../../tables/stock/TransferOrderAllocationTable';
import { StockDetailsPanel } from './StockDetailsPanel';

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
      path_detail: true,
      tags: true
    }
  });

  const { instance: part } = useInstance({
    endpoint: ApiEndpoints.part_list,
    pk: stockitem?.part,
    hasPrimaryKey: true,
    defaultValue: {}
  });

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

  const showTransferAllocations: boolean = useMemo(() => {
    return (
      !stockitem?.part_detail?.virtual &&
      globalSettings.isSet('TRANSFERORDER_ENABLED')
    );
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
        content: (
          <StockDetailsPanel
            instance={stockitem}
            allowImageEdit
            showSerialNav
            refreshInstance={refreshInstance}
          />
        )
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
          (!showSalesAllocations &&
            !showBuildAllocations &&
            !showTransferAllocations),
        content: (
          <Accordion
            multiple={true}
            defaultValue={[
              'buildAllocations',
              'salesAllocations',
              'transferAllocations'
            ]}
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
            {showTransferAllocations && (
              <Accordion.Item
                value='transferAllocations'
                key='transferAllocations'
              >
                <Accordion.Control>
                  <StylishText size='lg'>{t`Transfer Order Allocations`}</StylishText>
                </Accordion.Control>
                <Accordion.Panel>
                  <TransferOrderAllocationTable
                    stockId={stockitem.pk}
                    modelField='order'
                    modelTarget={ModelType.transferorder}
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
    queryParams: new URLSearchParams({ tags: 'true' }),
    onFormSuccess: refreshInstance
  });

  const convertStockItemFields: ApiFormFieldSet = useMemo(() => {
    return {
      part: {
        filters: {
          active: true,
          convert_from: stockitem.part
        }
      }
    };
  }, [stockitem]);

  const convertStockItem = useCreateApiFormModal({
    url: ApiEndpoints.stock_convert,
    pk: stockitem.pk,
    title: t`Convert Stock Item`,
    modalId: 'convert-stock-item',
    fields: convertStockItemFields,
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
    changeBatch: false,
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
    const serial = stockitem.serial;
    const serialized =
      serial != null &&
      serial != undefined &&
      serial != '' &&
      stockitem.quantity == 1;

    // Allow variant conversion if the part is a variant, or if the part is a template
    const canConvert = part?.variant_of || part?.is_template;

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
          {
            name: t`Convert`,
            tooltip: t`Convert this stock item to a different part`,
            hidden: !user.hasChangeRole(UserRoles.stock) || !canConvert,
            icon: <IconTransform color='blue' />,
            onClick: () => convertStockItem.open()
          },
          DeleteItemAction({
            hidden: !user.hasDeleteRole(UserRoles.stock),
            onClick: () => deleteStockItem.open()
          })
        ]}
      />
    ];
  }, [id, stockitem, part, user, stockAdjustActions.menuActions]);

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
              childIdentifier='sublocations'
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
      {deleteStockItem.modal}
      {convertStockItem.modal}
      {duplicateStockItem.modal}
      {serializeStockItem.modal}
      {stockAdjustActions.modals.map((modal) => modal.modal)}
      {orderPartsWizard.wizard}
    </>
  );
}
