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
  IconPackageOff
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
}

const ACCENT_GRADIENTS: Record<string, string> = {
  blue: 'linear-gradient(90deg, #0284c7 0%, #38bdf8 60%, #818cf8 100%)',
  teal: 'linear-gradient(90deg, #0d9488 0%, #2dd4bf 60%, #34d399 100%)',
  orange: 'linear-gradient(90deg, #ea580c 0%, #f59e0b 60%, #fbbf24 100%)',
  red: 'linear-gradient(90deg, #dc2626 0%, #f87171 60%, #fb7185 100%)'
};

function StatCard({
  label,
  endpoint,
  params,
  icon,
  color,
  link
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
      radius='md'
      style={{
        position: 'relative',
        overflow: 'hidden',
        height: '100%',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        gap: 6,
        padding: '14px 16px',
        cursor: link ? 'pointer' : 'default',
        background: isDark ? '#1e293b' : '#ffffff',
        border: isDark ? '1px solid rgba(255,255,255,0.08)' : '1.5px solid #e2e8f0',
        borderRadius: 14,
        boxShadow: isDark
          ? '0 2px 8px rgba(0,0,0,0.25)'
          : '0 2px 6px rgba(15, 23, 42, 0.04)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
      }}
      onClick={(e: any) => link && navigateToLink(link, navigate, e)}
      className={`stat-card-hover stat-card-hover-${color}`}
    >
      {/* Top border accent line matching Ref Image 3 */}
      <Box
        className='stat-card-top-accent'
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 3.5,
          background: ACCENT_GRADIENTS[color] ?? ACCENT_GRADIENTS.blue,
          borderRadius: '4px 4px 0 0',
          transformOrigin: 'left center',
          transform: 'scaleX(0)',
          opacity: 0,
          transition:
            'transform 0.55s cubic-bezier(0.25, 1, 0.5, 1), opacity 0.45s ease'
        }}
      />
      <Group justify='space-between' wrap='nowrap' align='center'>
        <Text
          size='xs'
          fw={700}
          c='dimmed'
          tt='uppercase'
          style={{ letterSpacing: '0.6px', fontSize: '0.72rem' }}
        >
          {label}
        </Text>
        <ThemeIcon
          size={32}
          radius='md'
          variant='light'
          color={color}
          style={{
            background: `color-mix(in srgb, var(--mantine-color-${color}-6) 14%, transparent)`
          }}
        >
          {icon}
        </ThemeIcon>
      </Group>

      {query.isLoading ? (
        <Skeleton height={32} width={70} radius='sm' />
      ) : (
        <Text
          style={{
            fontSize: '1.85rem',
            fontWeight: 800,
            lineHeight: 1,
            color: `var(--mantine-color-${color}-${isDark ? '4' : '7'})`
          }}
        >
          {(query.data ?? 0).toLocaleString()}
        </Text>
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
      link: '/part/category/index/parts'
    },
    {
      label: t`Available Stock`,
      endpoint: apiUrl(ApiEndpoints.stock_item_list),
      params: { in_stock: true },
      icon: <IconChartBar size={18} />,
      color: 'teal',
      link: '/stock/location/index/stock-items'
    },
    {
      label: t`Low Stock`,
      endpoint: apiUrl(ApiEndpoints.part_list),
      params: { low_stock: true, active: true, virtual: false },
      icon: <IconAlertTriangle size={18} />,
      color: 'orange',
      link: '/part/category/index/parts?low_stock=true'
    },
    {
      label: t`Out of Stock`,
      endpoint: apiUrl(ApiEndpoints.part_list),
      params: { active: true, virtual: false, has_stock: false },
      icon: <IconPackageOff size={18} />,
      color: 'red',
      link: '/part/category/index/parts?has_stock=false'
    }
  ];

  return (
    <Box style={{ width: '100%', height: '100%', boxSizing: 'border-box' }}>
      <style>{`
        .stat-card-hover {
          position: relative !important;
          overflow: hidden !important;
          transition: transform 0.5s cubic-bezier(0.25, 1, 0.5, 1),
                      box-shadow 0.5s cubic-bezier(0.25, 1, 0.5, 1),
                      border-color 0.45s ease !important;
        }
        .stat-card-hover:hover {
          transform: translateY(-3px) !important;
          box-shadow: 0 14px 28px -4px rgba(15, 23, 42, 0.1) !important;
        }
        [data-mantine-color-scheme='dark'] .stat-card-hover:hover {
          box-shadow: 0 14px 28px -4px rgba(0, 0, 0, 0.5) !important;
        }
        .stat-card-hover:hover .stat-card-top-accent {
          transform: scaleX(1) !important;
          opacity: 1 !important;
        }
        .stat-card-hover-blue:hover {
          border-color: rgba(2, 132, 199, 0.45) !important;
        }
        .stat-card-hover-teal:hover {
          border-color: rgba(13, 148, 136, 0.45) !important;
        }
        .stat-card-hover-orange:hover {
          border-color: rgba(234, 88, 12, 0.45) !important;
        }
        .stat-card-hover-red:hover {
          border-color: rgba(220, 38, 38, 0.45) !important;
        }
        .stat-card-hover:hover .mantine-ThemeIcon-root {
          transform: scale(1.08);
          transition: transform 0.25s ease !important;
        }
      `}</style>
      <SimpleGrid cols={4} spacing='md' style={{ height: '100%' }}>
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
