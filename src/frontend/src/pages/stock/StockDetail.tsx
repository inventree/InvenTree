import { t } from '@lingui/macro';
import { Alert, LoadingOverlay, Stack, Text } from '@mantine/core';
import {
  IconBookmark,
  IconBoxPadding,
  IconHistory,
  IconInfoCircle,
  IconNotes,
  IconPaperclip,
  IconSitemap,
  IconTransferIn
} from '@tabler/icons-react';
import { useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { PlaceholderPanel } from '../../components/items/Placeholder';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { AttachmentTable } from '../../components/tables/AttachmentTable';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { useInstance } from '../../hooks/UseInstance';

export default function StockDetail() {
  const { id } = useParams();

  const {
    instance: stockitem,
    refreshInstance,
    instanceQuery
  } = useInstance({
    url: '/stock/',
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
        icon: <IconInfoCircle />
      },
      {
        name: 'tracking',
        label: t`Stock Tracking`,
        icon: <IconHistory />
      },
      {
        name: 'allocations',
        label: t`Allocations`,
        icon: <IconBookmark />
      },
      {
        name: 'installed_items',
        label: t`Installed Items`,
        icon: <IconBoxPadding />
      },
      {
        name: 'child_items',
        label: t`Child Items`,
        icon: <IconSitemap />
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip />,
        content: (
          <AttachmentTable
            url="/stock/attachment/"
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
            url={`/stock/${stockitem.pk}/`}
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
