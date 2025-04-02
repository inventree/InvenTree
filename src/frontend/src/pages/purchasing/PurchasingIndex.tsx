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
import SegmentedIconControl from '../../components/buttons/SegmentedIconControl';
import OrderCalendar from '../../components/calendar/OrderCalendar';
import PermissionDenied from '../../components/errors/PermissionDenied';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/panels/PanelGroup';
import { useUserState } from '../../states/UserState';
import { CompanyTable } from '../../tables/company/CompanyTable';
import { ManufacturerPartTable } from '../../tables/purchasing/ManufacturerPartTable';
import { PurchaseOrderTable } from '../../tables/purchasing/PurchaseOrderTable';
import { SupplierPartTable } from '../../tables/purchasing/SupplierPartTable';

function PurchaseOrderOverview({
  view
}: {
  view: string;
}) {
  switch (view) {
    case 'calendar':
      return (
        <OrderCalendar
          model={ModelType.purchaseorder}
          role={UserRoles.purchase_order}
          params={{ outstanding: true }}
        />
      );
    case 'table':
    default:
      return <PurchaseOrderTable />;
  }
}

export default function PurchasingIndex() {
  const user = useUserState();

  const [purchaseOrderView, setpurchaseOrderView] = useLocalStorage<string>({
    key: 'purchaseOrderView',
    defaultValue: 'table'
  });

  const panels = useMemo(() => {
    return [
      {
        name: 'purchaseorders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />,
        hidden: !user.hasViewRole(UserRoles.purchase_order),
        content: <PurchaseOrderOverview view={purchaseOrderView} />,
        controls: (
          <SegmentedIconControl
            value={purchaseOrderView}
            onChange={setpurchaseOrderView}
            data={[
              { value: 'table', label: t`Table View`, icon: <IconTable /> },
              {
                value: 'calendar',
                label: t`Calendar View`,
                icon: <IconCalendar />
              }
            ]}
          />
        )
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
