import { t } from '@lingui/core/macro';
import { Stack } from '@mantine/core';
import {
  IconBuildingStore,
  IconCalendar,
  IconTable,
  IconTruckDelivery,
  IconTruckReturn
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
import { ReturnOrderTable } from '../../tables/sales/ReturnOrderTable';
import { SalesOrderTable } from '../../tables/sales/SalesOrderTable';

function SalesOrderOverview({
  view
}: {
  view: string;
}) {
  switch (view) {
    case 'calendar':
      return (
        <OrderCalendar
          model={ModelType.salesorder}
          role={UserRoles.sales_order}
          params={{ outstanding: true }}
        />
      );
    case 'table':
    default:
      return <SalesOrderTable />;
  }
}

function ReturnOrderOverview({
  view
}: {
  view: string;
}) {
  switch (view) {
    case 'calendar':
      return (
        <OrderCalendar
          model={ModelType.returnorder}
          role={UserRoles.return_order}
          params={{ outstanding: true }}
        />
      );
    case 'table':
    default:
      return <ReturnOrderTable />;
  }
}

export default function SalesIndex() {
  const user = useUserState();

  const [salesOrderView, setSalesOrderView] = useLocalStorage<string>({
    key: 'salesOrderView',
    defaultValue: 'table'
  });

  const [returnOrderView, setReturnOrderView] = useLocalStorage<string>({
    key: 'returnOrderView',
    defaultValue: 'table'
  });

  const panels = useMemo(() => {
    return [
      {
        name: 'salesorders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery />,
        content: <SalesOrderOverview view={salesOrderView} />,
        controls: (
          <SegmentedIconControl
            value={salesOrderView}
            onChange={setSalesOrderView}
            data={[
              { value: 'table', label: t`Table View`, icon: <IconTable /> },
              {
                value: 'calendar',
                label: t`Calendar View`,
                icon: <IconCalendar />
              }
            ]}
          />
        ),
        hidden: !user.hasViewRole(UserRoles.sales_order)
      },
      {
        name: 'returnorders',
        label: t`Return Orders`,
        icon: <IconTruckReturn />,
        content: <ReturnOrderOverview view={returnOrderView} />,
        controls: (
          <SegmentedIconControl
            value={returnOrderView}
            onChange={setReturnOrderView}
            data={[
              { value: 'table', label: t`Table View`, icon: <IconTable /> },
              {
                value: 'calendar',
                label: t`Calendar View`,
                icon: <IconCalendar />
              }
            ]}
          />
        ),
        hidden: !user.hasViewRole(UserRoles.return_order)
      },
      {
        name: 'customers',
        label: t`Customers`,
        icon: <IconBuildingStore />,
        content: (
          <CompanyTable path='sales/customer' params={{ is_customer: true }} />
        )
      }
    ];
  }, [user, salesOrderView, returnOrderView]);

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
