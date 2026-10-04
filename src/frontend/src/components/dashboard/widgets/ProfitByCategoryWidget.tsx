import { t } from '@lingui/core/macro';
import {
  Box,
  Center,
  Group,
  Loader,
  Select,
  Stack,
  Text,
  useMantineColorScheme
} from '@mantine/core';
import { useDocumentVisibility } from '@mantine/hooks';
import { DonutChart } from '@mantine/charts';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { useApi } from '../../../contexts/ApiContext';
import type { DashboardWidgetProps } from '../DashboardWidget';

const CHART_COLORS = [
  '#4dabf7',
  '#ffd43b',
  '#69db7c',
  '#f783ac',
  '#845ef7',
  '#ff8787',
  '#74c0fc',
  '#a9e34b'
];

function ProfitByCategoryChart() {
  const api = useApi();
  const visibility = useDocumentVisibility();
  const { colorScheme } = useMantineColorScheme();
  const isDark = colorScheme === 'dark';

  // Fetch categories
  const categoriesQuery = useQuery({
    queryKey: ['dashboard-part-categories', visibility],
    enabled: visibility === 'visible',
    staleTime: 10 * 60 * 1000,
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.category_list), {
          params: { top_level: true, limit: 8 }
        })
        .then((res) => res.data?.results ?? [])
  });

  // Fetch part counts per category (total parts)
  const partCountsQuery = useQuery({
    queryKey: ['dashboard-category-parts', categoriesQuery.data],
    enabled: !!categoriesQuery.data?.length,
    staleTime: 10 * 60 * 1000,
    queryFn: async () => {
      const categories = categoriesQuery.data ?? [];

      if (!categories.length) return [];

      const results = await Promise.all(
        categories.slice(0, 6).map(async (cat: any) => {
          const res = await api.get(apiUrl(ApiEndpoints.part_list), {
            params: { category: cat.pk, active: true, limit: 1 }
          });
          return {
            name: cat.name,
            value: res.data?.count ?? 0,
            color: ''
          };
        })
      );

      // Filter out empty categories and assign colors
      return results
        .filter((r) => r.value > 0)
        .map((r, i) => ({ ...r, color: CHART_COLORS[i % CHART_COLORS.length] }));
    }
  });

  const totalValue = (partCountsQuery.data ?? []).reduce(
    (sum: number, d: any) => sum + d.value,
    0
  );

  const isLoading = categoriesQuery.isLoading || partCountsQuery.isLoading;

  if (isLoading) {
    return (
      <Center style={{ height: '100%' }}>
        <Loader size='md' />
      </Center>
    );
  }

  const chartData = partCountsQuery.data ?? [];

  if (!chartData.length) {
    return (
      <Center style={{ height: '100%' }}>
        <Text c='dimmed' size='sm'>
          {t`No category data available`}
        </Text>
      </Center>
    );
  }

  return (
    <Box style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Group justify='space-between' mb='md'>
        <Text fw={700} size='md'>
          {t`Parts by Category`}
        </Text>
        <Text size='xs' c='dimmed'>
          {t`This Year`}
        </Text>
      </Group>

      <Group
        align='center'
        justify='space-between'
        style={{ flex: 1 }}
        wrap='nowrap'
        gap='xl'
      >
        {/* Donut chart */}
        <Box style={{ position: 'relative', flexShrink: 0 }}>
          <DonutChart
            data={chartData}
            size={160}
            thickness={32}
            withLabelsLine={false}
            withTooltip
            tooltipDataSource='segment'
          />
          <Box
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              pointerEvents: 'none'
            }}
          >
            <Text fw={800} size='xl' lh={1}>
              {totalValue.toLocaleString()}
            </Text>
            <Text size='xs' c='dimmed' fw={500}>
              {t`Total Parts`}
            </Text>
          </Box>
        </Box>

        {/* Legend */}
        <Stack gap={6} style={{ flex: 1, minWidth: 0 }}>
          {chartData.map((item: any) => (
            <Group
              key={item.name}
              justify='space-between'
              wrap='nowrap'
              gap='xs'
            >
              <Group gap='xs' wrap='nowrap' style={{ minWidth: 0 }}>
                <Box
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    background: item.color,
                    flexShrink: 0
                  }}
                />
                <Text size='xs' truncate fw={500} style={{ maxWidth: 120 }}>
                  {item.name} ({Math.round((item.value / totalValue) * 100)}%)
                </Text>
              </Group>
              <Text size='xs' fw={700} c={isDark ? 'gray.3' : 'gray.8'}>
                {item.value.toLocaleString()}
              </Text>
            </Group>
          ))}
        </Stack>
      </Group>
    </Box>
  );
}

export default function ProfitByCategoryWidget(): DashboardWidgetProps {
  return {
    label: 'dash-profit-cat',
    title: t`Parts by Category`,
    description: t`Distribution of parts across top-level categories`,
    minWidth: 4,
    minHeight: 4,
    render: () => <ProfitByCategoryChart />
  };
}
