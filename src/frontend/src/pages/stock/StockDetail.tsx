import { t } from '@lingui/macro';
import { Alert, LoadingOverlay, Stack, Text } from '@mantine/core';
import {
  IconBookmark,
  IconBoxPadding,
  IconChecklist,
  IconCircleCheck,
  IconCircleMinus,
  IconCirclePlus,
  IconCopy,
  IconDots,
  IconEdit,
  IconHistory,
  IconInfoCircle,
  IconLink,
  IconNotes,
  IconPackages,
  IconPaperclip,
  IconQrcode,
  IconSitemap,
  IconTransfer,
  IconTrash,
  IconUnlink
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import {
  ActionDropdown,
  BarcodeActionDropdown
} from '../../components/items/ActionDropdown';
import { PlaceholderPanel } from '../../components/items/Placeholder';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { StockLocationTree } from '../../components/nav/StockLocationTree';
import { AttachmentTable } from '../../components/tables/general/AttachmentTable';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { editStockItem } from '../../forms/StockForms';
import { useInstance } from '../../hooks/UseInstance';
import { ApiPaths, apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';

export default function StockDetail() {
  const { id } = useParams();

  const user = useUserState();

  const [treeOpen, setTreeOpen] = useState(false);

  const {
    instance: stockitem,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: ApiPaths.stock_item_list,
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
        content: <PlaceholderPanel />,
        hidden: !stockitem?.part_detail?.assembly
      },
      {
        name: 'child_items',
        label: t`Child Items`,
        icon: <IconSitemap />,
        content: <PlaceholderPanel />
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip />,
        content: (
          <AttachmentTable
            endpoint={ApiPaths.stock_attachment_list}
            model="stock_item"
            pk={stockitem.pk ?? -1}
          />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes />,
        content: (
          <NotesEditor
            url={apiUrl(ApiPaths.stock_item_list, stockitem.pk)}
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

  const stockActions = useMemo(
    () => /* TODO: Disable actions based on user permissions*/ [
      <BarcodeActionDropdown
        actions={[
          {
            icon: <IconQrcode />,
            name: t`View`,
            tooltip: t`View part barcode`
          },
          {
            icon: <IconLink />,
            name: t`Link Barcode`,
            tooltip: t`Link custom barcode to stock item`,
            disabled: stockitem?.barcode_hash
          },
          {
            icon: <IconUnlink />,
            name: t`Unlink Barcode`,
            tooltip: t`Unlink custom barcode from stock item`,
            disabled: !stockitem?.barcode_hash
          }
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
          {
            name: t`Edit`,
            tooltip: t`Edit stock item`,
            icon: <IconEdit color="blue" />,
            onClick: () => {
              stockitem.pk &&
                editStockItem({
                  item_id: stockitem.pk,
                  callback: () => refreshInstance
                });
            }
          },
          {
            name: t`Delete`,
            tooltip: t`Delete stock item`,
            icon: <IconTrash color="red" />
          }
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
    </Stack>
  );
}
