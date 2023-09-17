import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import { IconPackages, IconSitemap } from '@tabler/icons-react';
import { useMemo } from 'react';

import { PlaceholderPanel } from '../../components/items/Placeholder';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { StockItemTable } from '../../components/tables/stock/StockItemTable';

export default function Stock() {
  const categoryPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'stock-items',
        label: t`Stock Items`,
        icon: <IconPackages size="18" />,
        content: <StockItemTable />
      },
      {
        name: 'sublocations',
        label: t`Sublocations`,
        icon: <IconSitemap size="18" />,
        content: <PlaceholderPanel />
      }
    ];
  }, []);

  return (
    <>
      <Stack>
        <PageDetail title={t`Stock Items`} />
        <PanelGroup panels={categoryPanels} />
      </Stack>
    </>
  );
}
