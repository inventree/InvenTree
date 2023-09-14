import { t } from '@lingui/macro';
import { LoadingOverlay, Stack } from '@mantine/core';
import {
  IconClipboardCheck,
  IconClipboardList,
  IconInfoCircle,
  IconList,
  IconListCheck,
  IconListTree,
  IconNotes,
  IconPaperclip
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import { api } from '../../App';
import { PlaceholderPill } from '../../components/items/Placeholder';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { AttachmentTable } from '../../components/tables/AttachmentTable';

export default function BuildDetail() {
  const { id } = useParams();

  // Build data
  const [build, setBuild] = useState<any>({});

  // Query hook for fetching build data
  const buildQuery = useQuery(['build', id], async () => {
    let url = `/build/${id}/`;

    return api
      .get(url)
      .then((response) => {
        setBuild(response.data);
      })
      .catch((error) => {
        console.error(error);
        setBuild({});
      });
  });

  const buildPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Build Details`,
        icon: <IconInfoCircle size="18" />,
        content: <PlaceholderPill />
      },
      {
        name: 'allocate-stock',
        label: t`Allocate Stock`,
        icon: <IconListCheck size="18" />,
        content: <PlaceholderPill />
      },
      {
        name: 'incomplete-outputs',
        label: t`Incomplete Outputs`,
        icon: <IconClipboardList size="18" />,
        content: <PlaceholderPill />
      },
      {
        name: 'complete-outputs',
        label: t`Complete Outputs`,
        icon: <IconClipboardCheck size="18" />,
        content: <PlaceholderPill />
      },
      {
        name: 'consumed-stock',
        label: t`Consumed Stock`,
        icon: <IconList size="18" />,
        content: <PlaceholderPill />
      },
      {
        name: 'chiold-orders',
        label: t`Child Build Orders`,
        icon: <IconListTree size="18" />,
        content: <PlaceholderPill />
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip size="18" />,
        content: buildAttachmentsTab()
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes size="18" />,
        content: <PlaceholderPill />
      }
    ];
  }, [build]);

  function buildAttachmentsTab() {
    return (
      <AttachmentTable
        url="/build/attachment/"
        model="build"
        pk={build.pk ?? -1}
      />
    );
  }

  return (
    <>
      <Stack spacing="xs">
        <LoadingOverlay visible={buildQuery.isFetching} />
        <PanelGroup panels={buildPanels} />
      </Stack>
    </>
  );
}
