import { Trans, t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import {
  IconCategory,
  IconListDetails,
  IconSitemap
} from '@tabler/icons-react';
import { useMemo } from 'react';

import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { PartListTable } from '../../components/tables/part/PartTable';

/**
 * Part index page
 */
export default function PartIndex() {
  const panels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'parts',
        label: t`Parts`,
        icon: <IconCategory size="18" />,
        content: <PartListTable />
      },
      {
        name: 'categories',
        label: t`Categories`,
        icon: <IconSitemap size="18" />,
        content: <PlaceholderPill />
      },
      {
        name: 'parameters',
        label: t`Parameters`,
        icon: <IconListDetails size="18" />,
        content: <PlaceholderPill />
      }
    ];
  }, []);

  return (
    <>
      <Stack>
        <PageDetail
          title={t`Parts`}
          breadcrumbs={
            [
              // {
              //   name: t`Parts`,
              //   url: '/part',
              // }
            ]
          }
        />
        <PanelGroup panels={panels} />
      </Stack>
    </>
  );
}
