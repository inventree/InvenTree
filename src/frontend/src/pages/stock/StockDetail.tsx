import { t } from '@lingui/macro';
import { Alert, LoadingOverlay, Skeleton, Stack, Text } from '@mantine/core';
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

import {
  ActionDropdown,
  BarcodeActionDropdown,
  DeleteItemAction,
  EditItemAction,
  LinkBarcodeAction,
  UnlinkBarcodeAction,
  ViewBarcodeAction
} from '../../components/items/ActionDropdown';
import { PlaceholderPanel } from '../../components/items/Placeholder';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { StockLocationTree } from '../../components/nav/StockLocationTree';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useEditStockItem } from '../../forms/StockForms';
import { useInstance } from '../../hooks/UseInstance';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { AttachmentTable } from '../../tables/general/AttachmentTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';

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

  const stockPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Details`,
        icon: <IconInfoCircle />,
        content: <PlaceholderPanel />
      },
      {
        name: 'tracking',
        label: t`Stock Tracking`,
        icon: <IconHistory />,
        content: <PlaceholderPanel />
      },
      {
        name: 'allocations',
        label: t`Allocations`,
        icon: <IconBookmark />,
        content: <PlaceholderPanel />,
        hidden:
          !stockitem?.part_detail?.salable && !stockitem?.part_detail?.component
      },
      {
        name: 'testdata',
        label: t`Test Data`,
        icon: <IconChecklist />,
        hidden: !stockitem?.part_detail?.trackable
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
