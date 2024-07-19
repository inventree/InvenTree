import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import {
  IconBuildingFactory2,
  IconBuildingStore,
  IconShoppingCart
} from '@tabler/icons-react';
import { useMemo } from 'react';

import PermissionDenied from '../../components/errors/PermissionDenied';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/nav/PanelGroup';
import { UserRoles } from '../../enums/Roles';
import { useUserState } from '../../states/UserState';
import { CompanyTable } from '../../tables/company/CompanyTable';
import { PurchaseOrderTable } from '../../tables/purchasing/PurchaseOrderTable';

export default function PurchasingIndex() {
  const user = useUserState();

  const panels = useMemo(() => {
    return [
      {
        name: 'purchaseorders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />,
        content: <PurchaseOrderTable />
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

  if (!user.isLoggedIn() || !user.hasViewRole(UserRoles.purchase_order)) {
    return <PermissionDenied />;
  }

  return (
    <Stack>
      <PageDetail title={t`Purchasing`} />
      <PanelGroup pageKey="purchasing-index" panels={panels} />
    </Stack>
  );
}
