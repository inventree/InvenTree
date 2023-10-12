import { t } from '@lingui/macro';
import { Alert, LoadingOverlay, Stack, Text } from '@mantine/core';
import {
  IconBookmark,
  IconBoxPadding,
  IconHistory,
  IconInfoCircle,
  IconNotes,
  IconPaperclip,
  IconSitemap
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { PlaceholderPanel } from '../../components/items/Placeholder';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { AttachmentTable } from '../../components/tables/AttachmentTable';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { useInstance } from '../../hooks/UseInstance';
import { ApiPaths, apiUrl } from '../../states/ApiState';

export default function StockDetail() {
  const { id } = useParams();

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
        icon: <IconInfoCircle size="18" />,
        content: <PlaceholderPanel />
      },
      {
        name: 'tracking',
        label: t`Stock Tracking`,
        icon: <IconHistory size="18" />,
        content: <PlaceholderPanel />
      },
      {
        name: 'allocations',
        label: t`Allocations`,
        icon: <IconBookmark size="18" />,
        content: <PlaceholderPanel />
      },
      {
        name: 'installed_items',
        label: t`Installed Items`,
        icon: <IconBoxPadding size="18" />,
        content: <PlaceholderPanel />
      },
      {
        name: 'child_items',
        label: t`Child Items`,
        icon: <IconSitemap size="18" />,
        content: <PlaceholderPanel />
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip size="18" />,
        content: (
          <AttachmentTable
            url={ApiPaths.stock_attachment_list}
            model="stock_item"
            pk={stockitem.pk ?? -1}
          />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes size="18" />,
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

  return (
    <Stack>
      <LoadingOverlay visible={instanceQuery.isFetching} />
      <PageDetail
        title={t`Stock Items`}
        subtitle={stockitem.part_detail?.full_name ?? 'name goes here'}
        detail={
          <Alert color="teal" title="Stock Item">
            <Text>Quantity: {stockitem.quantity ?? 'idk'}</Text>
          </Alert>
        }
        breadcrumbs={breadcrumbs}
      />
      <PanelGroup panels={stockPanels} />
    </Stack>
  );
}
