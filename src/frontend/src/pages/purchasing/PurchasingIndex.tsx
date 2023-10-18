import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import {
  IconBuildingFactory2,
  IconBuildingStore,
  IconShoppingCart
} from '@tabler/icons-react';
import { useMemo } from 'react';

import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/nav/PanelGroup';
import { CompanyTable } from '../../components/tables/general/CompanyTable';

export default function PurchasingIndex() {
  const panels = useMemo(() => {
    return [
      {
        name: 'purchaseorders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />
      },
      {
        name: 'suppliers',
        label: t`Suppliers`,
        icon: <IconBuildingStore />,
        content: <CompanyTable params={{ is_supplier: true }} />
      },
      {
        name: 'manufacturer',
        label: t`Manufacturers`,
        icon: <IconBuildingFactory2 />,
        content: <CompanyTable params={{ is_manufacturer: true }} />
      }
    ];
  }, []);

  return (
    <>
      <Stack>
        <PageDetail title={t`Purchasing`} />
        <PanelGroup pageKey="purchasing-index" panels={panels} />
      </Stack>
    </>
  );
}
