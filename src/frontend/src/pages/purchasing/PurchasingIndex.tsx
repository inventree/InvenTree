import { t } from '@lingui/core/macro';
import { Stack } from '@mantine/core';
import {
  IconBuildingFactory2,
  IconBuildingStore,
  IconBuildingWarehouse,
  IconCalendar,
  IconPackageExport,
  IconShoppingCart,
  IconTable
} from '@tabler/icons-react';
import { useMemo } from 'react';

import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { useLocalStorage } from '@mantine/hooks';
import OrderCalendar from '../../components/calendar/OrderCalendar';
import PermissionDenied from '../../components/errors/PermissionDenied';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/panels/PanelGroup';
import SegmentedControlPanel from '../../components/panels/SegmentedControlPanel';
import { useUserState } from '../../states/UserState';
import { CompanyTable } from '../../tables/company/CompanyTable';
import { ManufacturerPartTable } from '../../tables/purchasing/ManufacturerPartTable';
import { PurchaseOrderTable } from '../../tables/purchasing/PurchaseOrderTable';
import { SupplierPartTable } from '../../tables/purchasing/SupplierPartTable';

export default function PurchasingIndex() {
  const user = useUserState();

  const [purchaseOrderView, setPurchaseOrderView] = useLocalStorage<string>({
    key: 'purchase-order-view',
    defaultValue: 'table'
  });

  const panels = useMemo(() => {
    return [
      SegmentedControlPanel({
        name: 'purchaseorders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />,
        hidden: !user.hasViewRole(UserRoles.purchase_order),
        selection: purchaseOrderView,
        onChange: setPurchaseOrderView,
        options: [
          {
            value: 'table',
            label: t`Table View`,
            icon: <IconTable />,
            content: <PurchaseOrderTable />
          },
          {
            value: 'calendar',
            label: t`Calendar View`,
            icon: <IconCalendar />,
            content: (
              <OrderCalendar
                model={ModelType.purchaseorder}
                role={UserRoles.purchase_order}
                params={{ outstanding: true }}
              />
            )
          }
        ]
      }),
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
        content: <SupplierPartTable />
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
        content: <ManufacturerPartTable />
      }
    ];
  }, [user, purchaseOrderView]);

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
