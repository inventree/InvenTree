import { t } from '@lingui/core/macro';
import { Stack } from '@mantine/core';
import {
  IconBuildingFactory2,
  IconBuildingStore,
  IconBuildingWarehouse,
  IconCalendar,
  IconListDetails,
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
import ParametricCompanyTable from '../../tables/company/ParametricCompanyTable';
import ManufacturerPartParametricTable from '../../tables/purchasing/ManufacturerPartParametricTable';
import { ManufacturerPartTable } from '../../tables/purchasing/ManufacturerPartTable';
import PurchaseOrderParametricTable from '../../tables/purchasing/PurchaseOrderParametricTable';
import { PurchaseOrderTable } from '../../tables/purchasing/PurchaseOrderTable';
import SupplierPartParametricTable from '../../tables/purchasing/SupplierPartParametricTable';
import { SupplierPartTable } from '../../tables/purchasing/SupplierPartTable';

export default function PurchasingIndex() {
  const user = useUserState();

  const [purchaseOrderView, setPurchaseOrderView] = useLocalStorage<string>({
    key: 'purchase-order-view',
    defaultValue: 'table'
  });

  const [supplierView, setSupplierView] = useLocalStorage<string>({
    key: 'supplier-view',
    defaultValue: 'table'
  });

  const [manufacturerView, setManufacturerView] = useLocalStorage<string>({
    key: 'manufacturer-view',
    defaultValue: 'table'
  });

  const [manufacturerPartsView, setManufacturerPartsView] =
    useLocalStorage<string>({
      key: 'manufacturer-parts-view',
      defaultValue: 'table'
    });

  const [supplierPartsView, setSupplierPartsView] = useLocalStorage<string>({
    key: 'supplier-parts-view',
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
          },
          {
            value: 'parametric',
            label: t`Parametric View`,
            icon: <IconListDetails />,
            content: <PurchaseOrderParametricTable />
          }
        ]
      }),
      SegmentedControlPanel({
        name: 'suppliers',
        label: t`Suppliers`,
        icon: <IconBuildingStore />,
        selection: supplierView,
        onChange: setSupplierView,
        options: [
          {
            value: 'table',
            label: t`Table View`,
            icon: <IconTable />,
            content: (
              <CompanyTable
                path='purchasing/supplier'
                params={{ is_supplier: true }}
              />
            )
          },
          {
            value: 'parametric',
            label: t`Parametric View`,
            icon: <IconListDetails />,
            content: (
              <ParametricCompanyTable queryParams={{ is_supplier: true }} />
            )
          }
        ]
      }),
      SegmentedControlPanel({
        name: 'supplier-parts',
        label: t`Supplier Parts`,
        icon: <IconPackageExport />,
        selection: supplierPartsView,
        onChange: setSupplierPartsView,
        options: [
          {
            value: 'table',
            label: t`Table View`,
            icon: <IconTable />,
            content: <SupplierPartTable />
          },
          {
            value: 'parametric',
            label: t`Parametric View`,
            icon: <IconListDetails />,
            content: <SupplierPartParametricTable />
          }
        ]
      }),
      SegmentedControlPanel({
        name: 'manufacturer',
        label: t`Manufacturers`,
        icon: <IconBuildingFactory2 />,
        selection: manufacturerView,
        onChange: setManufacturerView,
        options: [
          {
            value: 'table',
            label: t`Table View`,
            icon: <IconTable />,
            content: (
              <CompanyTable
                path='purchasing/manufacturer'
                params={{ is_manufacturer: true }}
              />
            )
          },
          {
            value: 'parametric',
            label: t`Parametric View`,
            icon: <IconListDetails />,
            content: (
              <ParametricCompanyTable queryParams={{ is_manufacturer: true }} />
            )
          }
        ]
      }),
      SegmentedControlPanel({
        name: 'manufacturer-parts',
        label: t`Manufacturer Parts`,
        icon: <IconBuildingWarehouse />,
        selection: manufacturerPartsView,
        onChange: setManufacturerPartsView,
        options: [
          {
            value: 'table',
            label: t`Table View`,
            icon: <IconTable />,
            content: <ManufacturerPartTable />
          },
          {
            value: 'parametric',
            label: t`Parametric View`,
            icon: <IconListDetails />,
            content: <ManufacturerPartParametricTable />
          }
        ]
      })
    ];
  }, [
    user,
    manufacturerPartsView,
    manufacturerView,
    purchaseOrderView,
    supplierPartsView,
    supplierView
  ]);

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
