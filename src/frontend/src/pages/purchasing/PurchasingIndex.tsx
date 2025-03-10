import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import {
  IconBuildingFactory2,
  IconBuildingStore,
  IconBuildingWarehouse,
  IconPackageExport,
  IconShoppingCart
} from '@tabler/icons-react';
import { useMemo } from 'react';

import PermissionDenied from '../../components/errors/PermissionDenied';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/panels/PanelGroup';
import { UserRoles } from '../../enums/Roles';
import { useUserState } from '../../states/UserState';
import { CompanyTable } from '../../tables/company/CompanyTable';
import { ManufacturerPartTable } from '../../tables/purchasing/ManufacturerPartTable';
import { PurchaseOrderTable } from '../../tables/purchasing/PurchaseOrderTable';
import { SupplierPartTable } from '../../tables/purchasing/SupplierPartTable';

export default function PurchasingIndex() {
  const user = useUserState();

  const panels = useMemo(() => {
    return [
      {
        name: 'purchaseorders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />,
        content: <PurchaseOrderTable />,
        hidden: !user.hasViewRole(UserRoles.purchase_order)
      },
      {
        name: 'suppliers',
        label: t`Suppliers`,
        icon: <IconBuildingStore />,
        content: (
          <CompanyTable
            path='purchasing/supplier'
            params={{ is_supplier: true }}
          />
        )
      },
      {
        name: 'supplier-parts',
        label: t`Supplier Parts`,
        icon: <IconPackageExport />,
        content: <SupplierPartTable params={{}} />
      },
      {
        name: 'manufacturer',
        label: t`Manufacturers`,
        icon: <IconBuildingFactory2 />,
        content: (
          <CompanyTable
            path='purchasing/manufacturer'
            params={{ is_manufacturer: true }}
          />
        )
      },
      {
        name: 'manufacturer-parts',
        label: t`Manufacturer Parts`,
        icon: <IconBuildingWarehouse />,
        content: <ManufacturerPartTable params={{}} />
      }
    ];
  }, [user]);

  if (!user.isLoggedIn() || !user.hasViewRole(UserRoles.purchase_order)) {
    return <PermissionDenied />;
  }

  return (
    <Stack>
      <PageDetail title={t`Purchasing`} />
      <PanelGroup
        pageKey='purchasing-index'
        panels={panels}
        model={'purchasing'}
        id={null}
      />
    </Stack>
  );
}
