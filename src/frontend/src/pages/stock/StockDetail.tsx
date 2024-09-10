import { t } from '@lingui/macro';
import { Accordion, Grid, Skeleton, Stack } from '@mantine/core';
import {
  IconBookmark,
  IconBoxPadding,
  IconChecklist,
  IconHistory,
  IconInfoCircle,
  IconNotes,
  IconPackages,
  IconPaperclip,
  IconSitemap
} from '@tabler/icons-react';
import { ReactNode, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import AdminButton from '../../components/buttons/AdminButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import { DetailsField, DetailsTable } from '../../components/details/Details';
import DetailsBadge from '../../components/details/DetailsBadge';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import NotesEditor from '../../components/editors/NotesEditor';
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
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import {
  StockOperationProps,
  useAddStockItem,
  useCountStockItem,
  useRemoveStockItem,
  useStockFields,
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
import { useUserState } from '../../states/UserState';
import BuildAllocatedStockTable from '../../tables/build/BuildAllocatedStockTable';
import { AttachmentTable } from '../../tables/general/AttachmentTable';
import SalesOrderAllocationTable from '../../tables/sales/SalesOrderAllocationTable';
import InstalledItemsTable from '../../tables/stock/InstalledItemsTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';
import StockItemTestResultTable from '../../tables/stock/StockItemTestResultTable';
import { StockTrackingTable } from '../../tables/stock/StockTrackingTable';

export default function StockDetail() {
  const { id } = useParams();

  const user = useUserState();

  const navigate = useNavigate();

  const [treeOpen, setTreeOpen] = useState(false);

  const {
    instance: stockitem,
    refreshInstance,
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
    let data = stockitem;
    let part = stockitem?.part_detail ?? {};

    data.available_stock = Math.max(0, data.quantity - data.allocated);

    if (instanceQuery.isFetching) {
      return <Skeleton />;
    }

    // Top left - core part information
    let tl: DetailsField[] = [
      {
        name: 'part',
        label: t`Base Part`,
        type: 'link',
        model: ModelType.part
      },
      {
        name: 'status',
        type: 'status',
        label: t`Stock Status`,
        model: ModelType.stockitem
      },
      {
        type: 'text',
        name: 'tests',
        label: `Completed Tests`,
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
    let tr: DetailsField[] = [
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
        icon: 'quantity'
      },
      {
        type: 'text',
        name: 'batch',
        label: t`Batch Code`,
        hidden: !stockitem.batch
      }
      // TODO: allocated_to_sales_orders
      // TODO: allocated_to_build_orders
    ];

    // Bottom left: location information
    let bl: DetailsField[] = [
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
        model_formatter: (model: any) => {
          let text = model?.part_detail?.full_name ?? model?.name;
          if (model.serial && model.quantity == 1) {
            text += `# ${model.serial}`;
          }

          return text;
        },
        icon: 'stock',
        model: ModelType.stockitem,
        hidden: !stockitem.belongs_to
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
    let br: DetailsField[] = [
      // TODO: Expiry date
      // TODO: Ownership
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
        <Grid>
          <Grid.Col span={4}>
            <DetailsImage
              appRole={UserRoles.part}
              apiPath={ApiEndpoints.part_list}
              src={
                stockitem.part_detail?.image ??
                stockitem?.part_detail?.thumbnail
              }
              pk={stockitem.part}
            />
          </Grid.Col>
          <Grid.Col span={8}>
            <DetailsTable fields={tl} item={stockitem} />
          </Grid.Col>
        </Grid>
        <DetailsTable fields={tr} item={stockitem} />
        <DetailsTable fields={bl} item={stockitem} />
        <DetailsTable fields={br} item={stockitem} />
      </ItemDetailsGrid>
    );
  }, [stockitem, instanceQuery]);

  const showBuildAllocations = useMemo(() => {
    // Determine if "build allocations" should be shown for this stock item
    return (
      stockitem?.part_detail?.component && // Must be a "component"
      !stockitem?.sales_order && // Must not be assigned to a sales order
      !stockitem?.belongs_to
    ); // Must not be installed into another item
  }, [stockitem]);

  const showSalesAlloctions = useMemo(() => {
    return stockitem?.part_detail?.salable;
  }, [stockitem]);

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
        hidden: !showSalesAlloctions && !showBuildAllocations,
        content: (
          <Accordion
            multiple={true}
            defaultValue={['buildallocations', 'salesallocations']}
          >
            {showBuildAllocations && (
              <Accordion.Item value="buildallocations" key="buildallocations">
                <Accordion.Control>
                  <StylishText size="lg">{t`Build Order Allocations`}</StylishText>
                </Accordion.Control>
                <Accordion.Panel>
                  <BuildAllocatedStockTable
                    stockId={stockitem.pk}
                    modelField="build"
                    modelTarget={ModelType.build}
                    showBuildInfo
                  />
                </Accordion.Panel>
              </Accordion.Item>
            )}
            {showSalesAlloctions && (
              <Accordion.Item value="salesallocations" key="salesallocations">
                <Accordion.Control>
                  <StylishText size="lg">{t`Sales Order Allocations`}</StylishText>
                </Accordion.Control>
                <Accordion.Panel>
                  <SalesOrderAllocationTable
                    stockId={stockitem.pk}
                    modelField="order"
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
        hidden: !stockitem?.part_detail?.assembly,
        content: <InstalledItemsTable parentId={stockitem.pk} />
      },
      {
        name: 'child_items',
        label: t`Child Items`,
        icon: <IconSitemap />,
        hidden: (stockitem?.child_items ?? 0) == 0,
        content: stockitem?.pk ? (
          <StockItemTable
            tableName="child-stock"
            params={{ ancestor: stockitem.pk }}
          />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip />,
        content: (
          <AttachmentTable
            model_type={ModelType.stockitem}
            model_id={stockitem.pk}
          />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes />,
        content: (
          <NotesEditor
            modelType={ModelType.stockitem}
            modelId={stockitem.pk}
            editable={user.hasChangeRole(UserRoles.stock)}
          />
        )
      }
    ];
  }, [stockitem, id, user]);

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

  const editStockItemFields = useStockFields({ create: false });

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
      items: stockitem,
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

  const stockActions = useMemo(
    () => [
      <AdminButton model={ModelType.stockitem} pk={stockitem.pk} />,
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
            icon: (
              <InvenTreeIcon icon="stocktake" iconProps={{ color: 'blue' }} />
            ),
            onClick: () => {
              stockitem.pk && countStockItem.open();
            }
          },
          {
            name: t`Add`,
            tooltip: t`Add stock`,
            icon: <InvenTreeIcon icon="add" iconProps={{ color: 'green' }} />,
            onClick: () => {
              stockitem.pk && addStockItem.open();
            }
          },
          {
            name: t`Remove`,
            tooltip: t`Remove stock`,
            icon: <InvenTreeIcon icon="remove" iconProps={{ color: 'red' }} />,
            onClick: () => {
              stockitem.pk && removeStockItem.open();
            }
          },
          {
            name: t`Transfer`,
            tooltip: t`Transfer stock`,
            icon: (
              <InvenTreeIcon icon="transfer" iconProps={{ color: 'blue' }} />
            ),
            onClick: () => {
              stockitem.pk && transferStockItem.open();
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
    ],
    [id, stockitem, user]
  );

  const stockBadges: ReactNode[] = useMemo(() => {
    let available = (stockitem?.quantity ?? 0) - (stockitem?.allocated ?? 0);
    available = Math.max(0, available);

    return instanceQuery.isLoading
      ? []
      : [
          <DetailsBadge
            color="yellow"
            label={t`In Production`}
            visible={stockitem.is_building}
          />,
          <DetailsBadge
            color="blue"
            label={t`Serial Number` + `: ${stockitem.serial}`}
            visible={!!stockitem.serial}
            key="serial"
          />,
          <DetailsBadge
            color="blue"
            label={t`Quantity` + `: ${stockitem.quantity}`}
            visible={!stockitem.serial}
            key="quantity"
          />,
          <DetailsBadge
            color="yellow"
            label={t`Available` + `: ${available}`}
            visible={!stockitem.serial && available != stockitem.quantity}
            key="available"
          />,
          <DetailsBadge
            color="blue"
            label={t`Batch Code` + `: ${stockitem.batch}`}
            visible={!!stockitem.batch}
            key="batch"
          />,
          <StatusRenderer
            status={stockitem.status_custom_key}
            type={ModelType.stockitem}
            options={{ size: 'lg' }}
            key="status"
          />
        ];
  }, [stockitem, instanceQuery]);

  return (
    <InstanceDetail status={requestStatus} loading={instanceQuery.isFetching}>
      <Stack>
        <NavigationTree
          title={t`Stock Locations`}
          modelType={ModelType.stocklocation}
          endpoint={ApiEndpoints.stock_location_tree}
          opened={treeOpen}
          onClose={() => setTreeOpen(false)}
          selectedId={stockitem?.location}
        />
        <PageDetail
          title={t`Stock Item`}
          subtitle={stockitem.part_detail?.full_name}
          imageUrl={stockitem.part_detail?.thumbnail}
          editAction={editStockItem.open}
          editEnabled={user.hasChangePermission(ModelType.stockitem)}
          badges={stockBadges}
          breadcrumbs={breadcrumbs}
          breadcrumbAction={() => {
            setTreeOpen(true);
          }}
          actions={stockActions}
        />
        <PanelGroup pageKey="stockitem" panels={stockPanels} />
        {editStockItem.modal}
        {duplicateStockItem.modal}
        {deleteStockItem.modal}
        {countStockItem.modal}
        {addStockItem.modal}
        {removeStockItem.modal}
        {transferStockItem.modal}
      </Stack>
    </InstanceDetail>
  );
}
