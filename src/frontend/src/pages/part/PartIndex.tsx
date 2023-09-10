import { Trans, t } from '@lingui/macro';
import { Group, Stack } from '@mantine/core';
import { IconListDetails, IconShape, IconSitemap } from '@tabler/icons-react';
import { useMemo } from 'react';

import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
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
        icon: <IconShape size="18" />,
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
      <Stack spacing="xs">
        <StylishText>
          <Trans>Parts</Trans>
        </StylishText>
        <PanelGroup panels={panels} />
      </Stack>
    </>
  );
}
