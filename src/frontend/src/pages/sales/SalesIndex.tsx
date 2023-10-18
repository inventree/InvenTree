import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import {
  IconBuildingStore,
  IconTruckDelivery,
  IconTruckReturn
} from '@tabler/icons-react';
import { useMemo } from 'react';

import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/nav/PanelGroup';

export default function PurchasingIndex() {
  const panels = useMemo(() => {
    return [
      {
        name: 'purchaseorders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery />
      },
      {
        name: 'returnorders',
        label: t`Return Orders`,
        icon: <IconTruckReturn />
      },
      {
        name: 'suppliers',
        label: t`Customers`,
        icon: <IconBuildingStore />
      }
    ];
  }, []);

  return (
    <>
      <Stack>
        <PageDetail title={t`Sales`} />
        <PanelGroup pageKey="sales-index" panels={panels} />
      </Stack>
    </>
  );
}
