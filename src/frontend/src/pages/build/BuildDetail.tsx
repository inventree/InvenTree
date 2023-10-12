import { t } from '@lingui/macro';
import { Alert, LoadingOverlay, Stack, Text } from '@mantine/core';
import {
  IconClipboardCheck,
  IconClipboardList,
  IconInfoCircle,
  IconList,
  IconListCheck,
  IconNotes,
  IconPaperclip,
  IconSitemap
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import {
  PlaceholderPanel,
  PlaceholderPill
} from '../../components/items/Placeholder';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { AttachmentTable } from '../../components/tables/AttachmentTable';
import { BuildOrderTable } from '../../components/tables/build/BuildOrderTable';
import { StockItemTable } from '../../components/tables/stock/StockItemTable';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { useInstance } from '../../hooks/UseInstance';
import { ApiPaths, apiUrl } from '../../states/ApiState';

/**
 * Detail page for a single Build Order
 */
export default function BuildDetail() {
  const { id } = useParams();

  const {
    instance: build,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: ApiPaths.build_order_list,
    pk: id,
    params: {
      part_detail: true
    }
  });

  const buildPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Build Details`,
        icon: <IconInfoCircle size="18" />,
        content: <PlaceholderPanel />
      },
      {
        name: 'allocate-stock',
        label: t`Allocate Stock`,
        icon: <IconListCheck size="18" />,
        content: <PlaceholderPanel />
        // TODO: Hide if build is complete
      },
      {
        name: 'incomplete-outputs',
        label: t`Incomplete Outputs`,
        icon: <IconClipboardList size="18" />,
        content: <PlaceholderPanel />
        // TODO: Hide if build is complete
      },
      {
        name: 'complete-outputs',
        label: t`Completed Outputs`,
        icon: <IconClipboardCheck size="18" />,
        content: (
          <StockItemTable
            params={{
              build: build.pk ?? -1,
              is_building: false
            }}
          />
        )
      },
      {
        name: 'consumed-stock',
        label: t`Consumed Stock`,
        icon: <IconList size="18" />,
        content: (
          <StockItemTable
            params={{
              consumed_by: build.pk ?? -1
            }}
          />
        )
      },
      {
        name: 'child-orders',
        label: t`Child Build Orders`,
        icon: <IconSitemap size="18" />,
        content: (
          <BuildOrderTable
            params={{
              parent: build.pk ?? -1
            }}
          />
        )
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip size="18" />,
        content: (
          <AttachmentTable
            url={ApiPaths.build_order_attachment_list}
            model="build"
            pk={build.pk ?? -1}
          />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes size="18" />,
        content: (
          <NotesEditor
            url={apiUrl(ApiPaths.build_order_list, build.pk)}
            data={build.notes ?? ''}
            allowEdit={true}
          />
        )
      }
    ];
  }, [build]);

  return (
    <>
      <Stack spacing="xs">
        <PageDetail
          title={t`Build Order`}
          subtitle={build.reference}
          detail={
            <Alert color="teal" title="Build order detail goes here">
              <Text>TODO: Build details</Text>
            </Alert>
          }
          breadcrumbs={[
            { name: t`Build Orders`, url: '/build' },
            { name: build.reference, url: `/build/${build.pk}` }
          ]}
          actions={[<PlaceholderPill key="1" />]}
        />
        <LoadingOverlay visible={instanceQuery.isFetching} />
        <PanelGroup panels={buildPanels} />
      </Stack>
    </>
  );
}
