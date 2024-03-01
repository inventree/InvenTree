import { t } from '@lingui/macro';
import {
  Alert,
  Grid,
  LoadingOverlay,
  Skeleton,
  Stack,
  Text
} from '@mantine/core';
import {
  IconBookmark,
  IconBoxPadding,
  IconChecklist,
  IconCircleCheck,
  IconCircleMinus,
  IconCirclePlus,
  IconCopy,
  IconDots,
  IconHistory,
  IconInfoCircle,
  IconNotes,
  IconPackages,
  IconPaperclip,
  IconSitemap,
  IconTransfer
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import { DetailsField, DetailsTable } from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import {
  ItemDetails,
  ItemDetailsGrid
} from '../../components/details/ItemDetails';
import {
  ActionDropdown,
  BarcodeActionDropdown,
  DeleteItemAction,
  EditItemAction,
  LinkBarcodeAction,
  UnlinkBarcodeAction,
  ViewBarcodeAction
} from '../../components/items/ActionDropdown';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { StockLocationTree } from '../../components/nav/StockLocationTree';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useEditStockItem } from '../../forms/StockForms';
import { useInstance } from '../../hooks/UseInstance';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { AttachmentTable } from '../../tables/general/AttachmentTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';
import StockItemTestResultTable from '../../tables/stock/StockItemTestResultTable';

export default function StockDetail() {
  const { id } = useParams();

  const user = useUserState();

  const [treeOpen, setTreeOpen] = useState(false);

  const {
    instance: stockitem,
    refreshInstance,
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

  const detailsPanel = useMemo(() => {
    let data = stockitem;

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
        type: 'text',
        label: t`Stock Status`
      },
      {
        type: 'text',
        name: 'tests',
        label: `Completed Tests`,
        icon: 'progress'
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
        label: t`Available`
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
        model: ModelType.stockitem,
        hidden: !stockitem.belongs_to
      },
      {
        type: 'link',
        name: 'consumed_by',
        label: t`Consumed By`,
        model: ModelType.build,
        hidden: !stockitem.consumed_by
      },
      {
        type: 'link',
        name: 'sales_order',
        label: t`Sales Order`,
        model: ModelType.salesorder,
        hidden: !stockitem.sales_order
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
        icon: <IconHistory />
      },
      {
        name: 'allocations',
        label: t`Allocations`,
        icon: <IconBookmark />,
        hidden:
          !stockitem?.part_detail?.salable && !stockitem?.part_detail?.component
      },
      {
        name: 'testdata',
        label: t`Test Data`,
        icon: <IconChecklist />,
        hidden: !stockitem?.part_detail?.trackable,
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
        hidden: !stockitem?.part_detail?.assembly
      },
      {
        name: 'child_items',
        label: t`Child Items`,
        icon: <IconSitemap />,
        hidden: (stockitem?.child_items ?? 0) == 0,
        content: stockitem?.pk ? (
          <StockItemTable params={{ ancestor: stockitem.pk }} />
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
            endpoint={ApiEndpoints.stock_attachment_list}
            model="stock_item"
            pk={Number(id)}
          />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes />,
        content: (
          <NotesEditor
            url={apiUrl(ApiEndpoints.stock_item_list, id)}
            data={stockitem.notes ?? ''}
            allowEdit={true}
          />
        )
      }
    ];
  }, [stockitem, id]);

  const breadcrumbs = useMemo(
    () => [
      { name: t`Stock`, url: '/stock' },
      ...(stockitem.location_path ?? []).map((l: any) => ({
        name: l.name,
        url: `/stock/location/${l.pk}`
      }))
    ],
    [stockitem]
  );

  const editStockItem = useEditStockItem({
    item_id: stockitem.pk,
    callback: () => refreshInstance()
  });

  const stockActions = useMemo(
    () => /* TODO: Disable actions based on user permissions*/ [
      <BarcodeActionDropdown
        actions={[
          ViewBarcodeAction({}),
          LinkBarcodeAction({
            disabled: stockitem?.barcode_hash
          }),
          UnlinkBarcodeAction({
            disabled: !stockitem?.barcode_hash
          })
        ]}
      />,
      <ActionDropdown
        key="operations"
        tooltip={t`Stock Operations`}
        icon={<IconPackages />}
        actions={[
          {
            name: t`Count`,
            tooltip: t`Count stock`,
            icon: <IconCircleCheck color="green" />
          },
          {
            name: t`Add`,
            tooltip: t`Add stock`,
            icon: <IconCirclePlus color="green" />
          },
          {
            name: t`Remove`,
            tooltip: t`Remove stock`,
            icon: <IconCircleMinus color="red" />
          },
          {
            name: t`Transfer`,
            tooltip: t`Transfer stock`,
            icon: <IconTransfer color="blue" />
          }
        ]}
      />,
      <ActionDropdown
        key="stock"
        // tooltip={t`Stock Actions`}
        icon={<IconDots />}
        actions={[
          {
            name: t`Duplicate`,
            tooltip: t`Duplicate stock item`,
            icon: <IconCopy />
          },
          EditItemAction({
            onClick: () => {
              stockitem.pk && editStockItem.open();
            }
          }),
          DeleteItemAction({})
        ]}
      />
    ],
    [id, stockitem, user]
  );

  return (
    <Stack>
      <LoadingOverlay visible={instanceQuery.isFetching} />
      <StockLocationTree
        opened={treeOpen}
        onClose={() => setTreeOpen(false)}
        selectedLocation={stockitem?.location}
      />
      <PageDetail
        title={t`Stock Item`}
        subtitle={stockitem.part_detail?.full_name}
        imageUrl={stockitem.part_detail?.thumbnail}
        detail={
          <Alert color="teal" title="Stock Item">
            <Text>Quantity: {stockitem.quantity ?? 'idk'}</Text>
          </Alert>
        }
        breadcrumbs={breadcrumbs}
        breadcrumbAction={() => {
          setTreeOpen(true);
        }}
        actions={stockActions}
      />
      <PanelGroup pageKey="stockitem" panels={stockPanels} />
      {editStockItem.modal}
    </Stack>
  );
}
