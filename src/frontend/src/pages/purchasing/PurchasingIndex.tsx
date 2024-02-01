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
import { CompanyTable } from '../../tables/company/CompanyTable';
import { PurchaseOrderTable } from '../../tables/purchasing/PurchaseOrderTable';

export default function PurchasingIndex() {
  const panels = useMemo(() => {
    return [
      {
        name: 'purchaseorders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />,
        content: <PurchaseOrderTable />
        // TODO: Add optional "calendar" display here...
      },
      {
        name: 'suppliers',
        label: t`Suppliers`,
        icon: <IconBuildingStore />,
        content: (
          <CompanyTable
            path="purchasing/supplier"
            params={{ is_supplier: true }}
          />
        )
      },
      {
        name: 'manufacturer',
        label: t`Manufacturers`,
        icon: <IconBuildingFactory2 />,
        content: (
          <CompanyTable
            path="purchasing/manufacturer"
            params={{ is_manufacturer: true }}
          />
        )
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
