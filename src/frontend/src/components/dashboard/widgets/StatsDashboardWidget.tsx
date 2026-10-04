import { t } from '@lingui/core/macro';
import {
  Box,
  Card,
  Group,
  SimpleGrid,
  Skeleton,
  Text,
  ThemeIcon,
  useMantineColorScheme
} from '@mantine/core';
import { useDocumentVisibility } from '@mantine/hooks';
import {
  IconAlertTriangle,
  IconChartBar,
  IconPackage,
  IconPackageOff,
  IconTrendingDown,
  IconTrendingUp
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { navigateToLink } from '@lib/functions/Navigation';
import { useApi } from '../../../contexts/ApiContext';
import type { DashboardWidgetProps } from '../DashboardWidget';

interface StatItem {
  label: string;
  endpoint: string;
  params: Record<string, any>;
  icon: React.ReactNode;
  color: string;
  link?: string;
  trend?: string;
  trendValue?: string;
  trendUp?: boolean;
}

function StatCard({
  label,
  endpoint,
  params,
  icon,
  color,
  link,
  trendValue,
  trendUp
}: Readonly<StatItem>) {
  const api = useApi();
  const navigate = useNavigate();
  const visibility = useDocumentVisibility();
  const { colorScheme } = useMantineColorScheme();
  const isDark = colorScheme === 'dark';

  const query = useQuery({
    queryKey: ['dashboard-stat', endpoint, params, visibility],
    enabled: visibility === 'visible',
    refetchOnMount: true,
    refetchInterval: 5 * 60 * 1000,
    staleTime: 3 * 60 * 1000,
    queryFn: () =>
      api
        .get(endpoint, { params: { ...params, limit: 1 } })
        .then((res) => res.data?.count ?? 0)
  });

  return (
    <Card
      withBorder
      shadow='sm'
      radius='md'
      padding='md'
      style={{
        cursor: link ? 'pointer' : 'default',
        transition: 'all 0.2s ease',
        background: isDark ? '#1e293b' : '#ffffff',
        border: isDark ? '1px solid rgba(255,255,255,0.08)' : '1.5px solid #e2e8f0',
        borderRadius: 16,
        boxShadow: isDark
          ? '0 4px 16px rgba(0,0,0,0.25)'
          : '0 4px 16px rgba(15, 23, 42, 0.04)'
      }}
      onClick={(e: any) => link && navigateToLink(link, navigate, e)}
      className='stat-card-hover'
    >
      <Group justify='space-between' wrap='nowrap' mb='xs'>
        <Text size='xs' fw={600} c='dimmed' tt='uppercase' style={{ letterSpacing: '0.5px' }}>
          {label}
        </Text>
        <ThemeIcon
          size='lg'
          radius='md'
          variant='light'
          color={color}
          style={{
            background: `color-mix(in srgb, var(--mantine-color-${color}-6) 15%, transparent)`
          }}
        >
          {icon}
        </ThemeIcon>
      </Group>

      {query.isLoading ? (
        <Skeleton height={36} width={80} radius='sm' mt='xs' />
      ) : (
        <Text
          style={{
            fontSize: '2rem',
            fontWeight: 800,
            lineHeight: 1,
            color: `var(--mantine-color-${color}-${isDark ? '4' : '7'})`
          }}
        >
          {(query.data ?? 0).toLocaleString()}
        </Text>
      )}

      {trendValue && (
        <Group gap='xs' mt={6}>
          {trendUp ? (
            <IconTrendingUp size={14} color={`var(--mantine-color-teal-5)`} />
          ) : (
            <IconTrendingDown size={14} color={`var(--mantine-color-red-5)`} />
          )}
          <Text size='xs' c={trendUp ? 'teal' : 'red'} fw={500}>
            {trendValue}
          </Text>
          <Text size='xs' c='dimmed'>
            {t`from last week`}
          </Text>
        </Group>
      )}
    </Card>
  );
}

function StatsRow() {
  const stats: StatItem[] = [
    {
      label: t`Total Products`,
      endpoint: apiUrl(ApiEndpoints.part_list),
      params: { active: true },
      icon: <IconPackage size={18} />,
      color: 'blue',
      link: '/part',
      trendValue: '+4.32%',
      trendUp: true
    },
    {
      label: t`Available Stock`,
      endpoint: apiUrl(ApiEndpoints.stock_item_list),
      params: { in_stock: true },
      icon: <IconChartBar size={18} />,
      color: 'teal',
      link: '/stock',
      trendValue: '-6.24%',
      trendUp: false
    },
    {
      label: t`Low Stock`,
      endpoint: apiUrl(ApiEndpoints.part_list),
      params: { low_stock: true, active: true, virtual: false },
      icon: <IconAlertTriangle size={18} />,
      color: 'orange',
      link: '/part?low_stock=true',
      trendValue: '+1.33%',
      trendUp: false
    },
    {
      label: t`Out of Stock`,
      endpoint: apiUrl(ApiEndpoints.part_list),
      params: { active: true, virtual: false, in_stock: false },
      icon: <IconPackageOff size={18} />,
      color: 'red',
      link: '/part?in_stock=false',
      trendValue: '-1.99%',
      trendUp: true
    }
  ];

  return (
    <Box style={{ width: '100%', height: '100%', padding: '4px 0' }}>
      <SimpleGrid cols={4} spacing='md'>
        {stats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </SimpleGrid>
    </Box>
  );
}

export default function StatsDashboardWidget(): DashboardWidgetProps {
  return {
    label: 'dash-stats',
    title: t`Overview Stats`,
    description: t`Key metrics: total products, stock levels, and alerts`,
    minWidth: 8,
    minHeight: 2,
    render: () => <StatsRow />
  };
}
