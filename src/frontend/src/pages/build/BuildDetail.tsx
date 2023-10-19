import { t } from '@lingui/macro';
import { Alert, LoadingOverlay, Stack, Text } from '@mantine/core';
import {
  IconClipboardCheck,
  IconClipboardList,
  IconCopy,
  IconDots,
  IconEdit,
  IconFileTypePdf,
  IconInfoCircle,
  IconLink,
  IconList,
  IconListCheck,
  IconNotes,
  IconPaperclip,
  IconPrinter,
  IconQrcode,
  IconSitemap,
  IconTrash,
  IconUnlink
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { ActionDropdown } from '../../components/items/ActionDropdown';
import {
  PlaceholderPanel,
  PlaceholderPill
} from '../../components/items/Placeholder';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { BuildOrderTable } from '../../components/tables/build/BuildOrderTable';
import { AttachmentTable } from '../../components/tables/general/AttachmentTable';
import { StockItemTable } from '../../components/tables/stock/StockItemTable';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { useInstance } from '../../hooks/UseInstance';
import { ApiPaths, apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';

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

  const user = useUserState();

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
            endpoint={ApiPaths.build_order_attachment_list}
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

  const buildActions = useMemo(() => {
    // TODO: Disable certain actions based on user permissions
    return [
      <ActionDropdown
        tooltip={t`Barcode Actions`}
        icon={<IconQrcode />}
        actions={[
          {
            icon: <IconQrcode />,
            name: t`View`,
            tooltip: t`View part barcode`
          },
          {
            icon: <IconLink />,
            name: t`Link Barcode`,
            tooltip: t`Link custom barcode to part`,
            disabled: build?.barcode_hash
          },
          {
            icon: <IconUnlink />,
            name: t`Unlink Barcode`,
            tooltip: t`Unlink custom barcode from part`,
            disabled: !build?.barcode_hash
          }
        ]}
      />,
      <ActionDropdown
        tooltip={t`Reporting Actions`}
        icon={<IconPrinter />}
        actions={[
          {
            icon: <IconFileTypePdf />,
            name: t`Report`,
            tooltip: t`Print build report`
          }
        ]}
      />,
      <ActionDropdown
        tooltip={t`Build Order Actions`}
        icon={<IconDots />}
        actions={[
          {
            icon: <IconEdit color="blue" />,
            name: t`Edit`,
            tooltip: t`Edit build order`
          },
          {
            icon: <IconCopy color="green" />,
            name: t`Duplicate`,
            tooltip: t`Duplicate build order`
          },
          {
            icon: <IconTrash color="red" />,
            name: t`Delete`,
            tooltip: t`Delete build order`
          }
        ]}
      />
    ];
  }, [id, build, user]);

  return (
    <>
      <Stack spacing="xs">
        <PageDetail
          title={t`Build Order`}
          subtitle={build.reference}
          breadcrumbs={[
            { name: t`Build Orders`, url: '/build' },
            { name: build.reference, url: `/build/${build.pk}` }
          ]}
          actions={buildActions}
        />
        <LoadingOverlay visible={instanceQuery.isFetching} />
        <PanelGroup pageKey="build" panels={buildPanels} />
      </Stack>
    </>
  );
}
