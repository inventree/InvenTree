import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Box,
  Group,
  Stack,
  Text,
  useMantineColorScheme
} from '@mantine/core';
import { IconDots } from '@tabler/icons-react';
import type { DashboardWidgetProps } from '../DashboardWidget';

interface TrafficItem {
  channel: string;
  share: number;
  lastWeek: number;
  color: string;
  points: number[];
}

const TRAFFIC_DATA: TrafficItem[] = [
  {
    channel: 'Amazon',
    share: 27,
    lastWeek: 26,
    color: '#10b981',
    points: [20, 28, 22, 35, 30, 48, 42, 58]
  },
  {
    channel: 'Ebay',
    share: 23,
    lastWeek: 25,
    color: '#ef4444',
    points: [52, 45, 48, 38, 40, 28, 32, 22]
  },
  {
    channel: 'Aliexpress',
    share: 18,
    lastWeek: 18,
    color: '#f59e0b',
    points: [30, 32, 29, 31, 30, 32, 30, 31]
  },
  {
    channel: 'Etsy',
    share: 10,
    lastWeek: 8,
    color: '#10b981',
    points: [15, 20, 18, 25, 22, 32, 28, 40]
  },
  {
    channel: 'Walmart',
    share: 8,
    lastWeek: 11,
    color: '#ef4444',
    points: [45, 40, 42, 35, 30, 22, 25, 18]
  }
];

function Sparkline({ points, color }: { points: number[]; color: string }) {
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const width = 80;
  const height = 30;

  const coords = points.map((p, i) => {
    const x = (i / (points.length - 1)) * width;
    const y = height - ((p - min) / range) * (height - 8) - 4;
    return { x, y };
  });

  // Generate smooth SVG curve
  let d = `M ${coords[0].x} ${coords[0].y}`;
  for (let i = 0; i < coords.length - 1; i++) {
    const p0 = coords[i];
    const p1 = coords[i + 1];
    const mx = (p0.x + p1.x) / 2;
    d += ` C ${mx} ${p0.y}, ${mx} ${p1.y}, ${p1.x} ${p1.y}`;
  }

  const fillD = `${d} L ${width} ${height} L 0 ${height} Z`;

  return (
    <svg width={width} height={height} style={{ overflow: 'visible' }}>
      <defs>
        <linearGradient id={`grad-${color.replace('#', '')}`} x1='0%' y1='0%' x2='0%' y2='100%'>
          <stop offset='0%' stopColor={color} stopOpacity={0.25} />
          <stop offset='100%' stopColor={color} stopOpacity={0.0} />
        </linearGradient>
      </defs>
      <path d={fillD} fill={`url(#grad-${color.replace('#', '')})`} />
      <path
        d={d}
        fill='none'
        stroke={color}
        strokeWidth='2'
        strokeLinecap='round'
        strokeLinejoin='round'
      />
    </svg>
  );
}

function TrafficSourceContent() {
  const { colorScheme } = useMantineColorScheme();
  const isDark = colorScheme === 'dark';

  return (
    <Box style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Group justify='space-between' align='center' mb='sm'>
        <Text fw={700} size='sm' c={isDark ? '#f8fafc' : '#0f172a'}>
          {t`Traffic Source`}
        </Text>
        <ActionIcon variant='subtle' color='gray' size='sm' radius='md'>
          <IconDots size={16} />
        </ActionIcon>
      </Group>

      <Stack gap='xs' style={{ flex: 1, justifyContent: 'space-around' }}>
        {TRAFFIC_DATA.map((item) => (
          <Group key={item.channel} justify='space-between' align='center' wrap='nowrap'>
            <Box style={{ minWidth: 80 }}>
              <Text size='xs' fw={600} c={isDark ? '#94a3b8' : '#64748b'}>
                {item.channel}
              </Text>
              <Group gap={6} align='baseline' wrap='nowrap'>
                <Text size='sm' fw={700} c={isDark ? '#f8fafc' : '#0f172a'}>
                  {item.share}%
                </Text>
                <Text size='10px' c='dimmed'>
                  {t`Last week: `}{item.lastWeek}%
                </Text>
              </Group>
            </Box>

            <Box style={{ flexShrink: 0 }}>
              <Sparkline points={item.points} color={item.color} />
            </Box>
          </Group>
        ))}
      </Stack>
    </Box>
  );
}

export default function TrafficSourceWidget(): DashboardWidgetProps {
  return {
    label: 'dash-traffic-source',
    title: t`Traffic Source`,
    description: t`Inventory traffic and sales channels distribution`,
    minWidth: 3,
    minHeight: 4,
    render: () => <TrafficSourceContent />
  };
}
