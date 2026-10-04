import { t } from '@lingui/core/macro';
import {
  Box,
  Center,
  Group,
  Loader,
  SegmentedControl,
  Text,
  useMantineColorScheme
} from '@mantine/core';
import { useDocumentVisibility } from '@mantine/hooks';
import { AreaChart } from '@mantine/charts';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { subDays, format } from 'date-fns';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { useApi } from '../../../contexts/ApiContext';
import type { DashboardWidgetProps } from '../DashboardWidget';

type Period = '7d' | '30d';

function buildDayBuckets(days: number): Record<string, number> {
  const buckets: Record<string, number> = {};
  for (let i = days - 1; i >= 0; i--) {
    const d = format(subDays(new Date(), i), 'MMM dd');
    buckets[d] = 0;
  }
  return buckets;
}

function OrderSummaryChart() {
  const api = useApi();
  const visibility = useDocumentVisibility();
  const [period, setPeriod] = useState<Period>('7d');
  const { colorScheme } = useMantineColorScheme();
  const isDark = colorScheme === 'dark';

  const days = period === '7d' ? 7 : 30;

  const ordersQuery = useQuery({
    queryKey: ['dashboard-order-summary', period, visibility],
    enabled: visibility === 'visible',
    staleTime: 5 * 60 * 1000,
    queryFn: async () => {
      const since = subDays(new Date(), days).toISOString().split('T')[0];

      const res = await api.get(apiUrl(ApiEndpoints.sales_order_list), {
        params: {
          min_date: since,
          ordering: 'creation_date',
          limit: 200
        }
      });

      return res.data?.results ?? [];
    }
  });

  const purchaseOrdersQuery = useQuery({
    queryKey: ['dashboard-po-summary', period, visibility],
    enabled: visibility === 'visible',
    staleTime: 5 * 60 * 1000,
    queryFn: async () => {
      const since = subDays(new Date(), days).toISOString().split('T')[0];

      const res = await api.get(apiUrl(ApiEndpoints.purchase_order_list), {
        params: {
          min_date: since,
          ordering: 'creation_date',
          limit: 200
        }
      });

      return res.data?.results ?? [];
    }
  });

  const isLoading = ordersQuery.isLoading || purchaseOrdersQuery.isLoading;

  const chartData = (() => {
    const soBuckets = buildDayBuckets(days);
    const poBuckets = buildDayBuckets(days);

    for (const order of ordersQuery.data ?? []) {
      const d = order.creation_date ?? order.target_date;
      if (!d) continue;
      const key = format(new Date(d), 'MMM dd');
      if (key in soBuckets) {
        soBuckets[key] = (soBuckets[key] ?? 0) + 1;
      }
    }

    for (const order of purchaseOrdersQuery.data ?? []) {
      const d = order.creation_date ?? order.target_date;
      if (!d) continue;
      const key = format(new Date(d), 'MMM dd');
      if (key in poBuckets) {
        poBuckets[key] = (poBuckets[key] ?? 0) + 1;
      }
    }

    return Object.keys(soBuckets).map((k) => ({
      date: k,
      'Sales Orders': soBuckets[k],
      'Purchase Orders': poBuckets[k]
    }));
  })();

  const totalSO = (ordersQuery.data ?? []).length;

  if (isLoading) {
    return (
      <Center style={{ height: '100%' }}>
        <Loader size='md' />
      </Center>
    );
  }

  return (
    <Box style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Group justify='space-between' mb='sm'>
        <Box>
          <Text fw={700} size='md'>
            {t`Order Summary`}
          </Text>
          <Text size='xs' c='dimmed' fw={500}>
            {totalSO} {t`Total Orders`}
          </Text>
        </Box>
        <SegmentedControl
          size='xs'
          value={period}
          onChange={(v) => setPeriod(v as Period)}
          data={[
            { label: t`7 Days`, value: '7d' },
            { label: t`30 Days`, value: '30d' }
          ]}
        />
      </Group>

      <Box style={{ flex: 1, minHeight: 0 }}>
        <AreaChart
          h='100%'
          data={chartData}
          dataKey='date'
          series={[
            { name: 'Sales Orders', color: 'blue.6' },
            { name: 'Purchase Orders', color: 'teal.5' }
          ]}
          curveType='natural'
          withDots={false}
          withGradient
          fillOpacity={0.2}
          gridAxis='x'
          tickLine='none'
          strokeWidth={2}
          style={{ fontSize: 11 }}
        />
      </Box>
    </Box>
  );
}

export default function OrderSummaryWidget(): DashboardWidgetProps {
  return {
    label: 'dash-order-summary',
    title: t`Order Summary`,
    description: t`Sales and purchase orders over time`,
    minWidth: 4,
    minHeight: 4,
    render: () => <OrderSummaryChart />
  };
}
