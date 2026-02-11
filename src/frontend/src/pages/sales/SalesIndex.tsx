import { t } from '@lingui/core/macro';
import { Stack } from '@mantine/core';
import {
  IconBuildingStore,
  IconCalendar,
  IconCubeSend,
  IconListDetails,
  IconTable,
  IconTruckDelivery,
  IconTruckReturn
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
import ReturnOrderParametricTable from '../../tables/sales/ReturnOrderParametricTable';
import { ReturnOrderTable } from '../../tables/sales/ReturnOrderTable';
import SalesOrderParametricTable from '../../tables/sales/SalesOrderParametricTable';
import SalesOrderShipmentTable from '../../tables/sales/SalesOrderShipmentTable';
import { SalesOrderTable } from '../../tables/sales/SalesOrderTable';

export default function SalesIndex() {
  const user = useUserState();

  const [customersView, setCustomersView] = useLocalStorage<string>({
    key: 'customer-view',
    defaultValue: 'table'
  });

  const [salesOrderView, setSalesOrderView] = useLocalStorage<string>({
    key: 'sales-order-view',
    defaultValue: 'table'
  });

  const [returnOrderView, setReturnOrderView] = useLocalStorage<string>({
    key: 'return-order-view',
    defaultValue: 'table'
  });

  const panels = useMemo(() => {
    return [
      SegmentedControlPanel({
        name: 'salesorders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery />,
        hidden: !user.hasViewRole(UserRoles.sales_order),
        selection: salesOrderView,
        onChange: setSalesOrderView,
        options: [
          {
            value: 'table',
            label: t`Table View`,
            icon: <IconTable />,
            content: <SalesOrderTable />
          },
          {
            value: 'calendar',
            label: t`Calendar View`,
            icon: <IconCalendar />,
            content: (
              <OrderCalendar
                model={ModelType.returnorder}
                role={UserRoles.return_order}
                params={{ outstanding: true }}
              />
            )
          },
          {
            value: 'parametric',
            label: t`Parametric View`,
            icon: <IconListDetails />,
            content: <SalesOrderParametricTable />
          }
        ]
      }),
      {
        name: 'shipments',
        label: t`Pending Shipments`,
        icon: <IconCubeSend />,
        content: (
          <SalesOrderShipmentTable
            tableName={'sales-order-pending-shipment'}
            showOrderInfo
            filters={{ shipped: false, order_outstanding: true }}
          />
        )
      },
      SegmentedControlPanel({
        name: 'returnorders',
        label: t`Return Orders`,
        icon: <IconTruckReturn />,
        hidden: !user.hasViewRole(UserRoles.return_order),
        selection: returnOrderView,
        onChange: setReturnOrderView,
        options: [
          {
            value: 'table',
            label: t`Table View`,
            icon: <IconTable />,
            content: <ReturnOrderTable />
          },
          {
            value: 'calendar',
            label: t`Calendar View`,
            icon: <IconCalendar />,
            content: (
              <OrderCalendar
                model={ModelType.returnorder}
                role={UserRoles.return_order}
                params={{ outstanding: true }}
              />
            )
          },
          {
            value: 'parametric',
            label: t`Parametric View`,
            icon: <IconListDetails />,
            content: <ReturnOrderParametricTable />
          }
        ]
      }),
      SegmentedControlPanel({
        name: 'customers',
        label: t`Customers`,
        icon: <IconBuildingStore />,
        selection: customersView,
        onChange: setCustomersView,
        options: [
          {
            value: 'table',
            label: t`Table View`,
            icon: <IconTable />,
            content: (
              <CompanyTable
                path='sales/customer'
                params={{ is_customer: true }}
              />
            )
          },
          {
            value: 'parametric',
            label: t`Parametric View`,
            icon: <IconListDetails />,
            content: (
              <ParametricCompanyTable queryParams={{ is_customer: true }} />
            )
          }
        ]
      })
    ];
  }, [user, customersView, salesOrderView, returnOrderView]);

  if (!user.isLoggedIn() || !user.hasViewRole(UserRoles.sales_order)) {
    return <PermissionDenied />;
  }

  return (
    <Stack>
      <PageDetail title={t`Sales`} />
      <PanelGroup
        pageKey='sales-index'
        panels={panels}
        model={'sales'}
        id={null}
      />
    </Stack>
  );
}
