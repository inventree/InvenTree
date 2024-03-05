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
import { CompanyTable } from '../../tables/company/CompanyTable';
import { ReturnOrderTable } from '../../tables/sales/ReturnOrderTable';
import { SalesOrderTable } from '../../tables/sales/SalesOrderTable';

export default function PurchasingIndex() {
  const panels = useMemo(() => {
    return [
      {
        name: 'salesorders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery />,
        content: <SalesOrderTable />
      },
      {
        name: 'returnorders',
        label: t`Return Orders`,
        icon: <IconTruckReturn />,
        content: <ReturnOrderTable />
      },
      {
        name: 'suppliers',
        label: t`Customers`,
        icon: <IconBuildingStore />,
        content: (
          <CompanyTable path="sales/customer" params={{ is_customer: true }} />
        )
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
