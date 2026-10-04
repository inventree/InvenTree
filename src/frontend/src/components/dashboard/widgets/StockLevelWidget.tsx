import { t } from '@lingui/core/macro';
import {
  Anchor,
  Badge,
  Box,
  Center,
  Group,
  Loader,
  Progress,
  Stack,
  Text,
  useMantineColorScheme
} from '@mantine/core';
import { useDocumentVisibility } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { navigateToLink } from '@lib/functions/Navigation';
import { useApi } from '../../../contexts/ApiContext';
import type { DashboardWidgetProps } from '../DashboardWidget';

function StockLevelContent() {
  const api = useApi();
  const navigate = useNavigate();
  const visibility = useDocumentVisibility();
  const { colorScheme } = useMantineColorScheme();
  const isDark = colorScheme === 'dark';

  const query = useQuery({
    queryKey: ['dashboard-stock-level', visibility],
    enabled: visibility === 'visible',
    staleTime: 5 * 60 * 1000,
    refetchInterval: 10 * 60 * 1000,
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.part_list), {
          params: {
            low_stock: true,
            active: true,
            virtual: false,
            limit: 6,
            ordering: 'total_in_stock'
          }
        })
        .then((res) => res.data?.results ?? [])
  });

  // Total stock count query
  const totalQuery = useQuery({
    queryKey: ['dashboard-total-stock', visibility],
    enabled: visibility === 'visible',
    staleTime: 5 * 60 * 1000,
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.stock_item_list), {
          params: { in_stock: true, limit: 1 }
        })
        .then((res) => res.data?.count ?? 0)
  });

  if (query.isLoading) {
    return (
      <Center style={{ height: '100%' }}>
        <Loader size='md' />
      </Center>
    );
  }

  const parts = query.data ?? [];
  const totalStock = totalQuery.data ?? 0;

  const getStockStatus = (part: any) => {
    const inStock = part.total_in_stock ?? 0;
    const minStock = part.minimum_stock ?? 0;
    if (inStock === 0) return { label: t`Out of Stock`, color: 'red' };
    if (inStock <= minStock) return { label: t`Low`, color: 'orange' };
    return { label: t`OK`, color: 'teal' };
  };

  return (
    <Box style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Group justify='space-between' mb='md'>
        <Box>
          <Text fw={700} size='md'>
            {t`Stock Level`}
          </Text>
          <Group gap='xs' mt={2}>
            <Text size='xs' c='dimmed'>
              {t`Total Stock`}
            </Text>
            <Text size='xs' fw={700}>
              {totalQuery.isLoading ? '—' : totalStock.toLocaleString()}
            </Text>
            {parts.length > 0 && (
              <Badge size='xs' color='orange' variant='light'>
                {t`Low Stock`}
              </Badge>
            )}
          </Group>
        </Box>
        <Anchor
          size='xs'
          fw={600}
          onClick={(e: any) => navigateToLink('/stock', navigate, e)}
        >
          {t`View All`}
        </Anchor>
      </Group>

      {parts.length === 0 ? (
        <Center style={{ flex: 1 }}>
          <Stack align='center' gap='xs'>
            <Text size='sm' c='teal' fw={600}>
              ✓ {t`All stock levels are sufficient`}
            </Text>
            <Text size='xs' c='dimmed'>
              {t`No parts with low stock found`}
            </Text>
          </Stack>
        </Center>
      ) : (
        <Stack gap='sm' style={{ flex: 1, overflow: 'auto' }}>
          {parts.map((part: any) => {
            const inStock = part.total_in_stock ?? 0;
            const minStock = part.minimum_stock ?? 0;
            const maxForBar = Math.max(minStock * 2, inStock, 10);
            const progressValue = Math.min((inStock / maxForBar) * 100, 100);
            const status = getStockStatus(part);

            return (
              <Box key={part.pk}>
                <Group justify='space-between' mb={4} wrap='nowrap'>
                  <Anchor
                    size='xs'
                    fw={600}
                    truncate
                    style={{ maxWidth: '60%' }}
                    onClick={(e: any) =>
                      navigateToLink(`/part/${part.pk}`, navigate, e)
                    }
                  >
                    {part.name}
                  </Anchor>
                  <Group gap='xs'>
                    <Text size='xs' c='dimmed'>
                      {inStock} / {minStock} {t`min`}
                    </Text>
                    <Badge size='xs' color={status.color} variant='light'>
                      {status.label}
                    </Badge>
                  </Group>
                </Group>
                <Progress
                  value={progressValue}
                  size='sm'
                  radius='xl'
                  color={status.color}
                  bg={isDark ? 'dark.5' : 'gray.2'}
                />
              </Box>
            );
          })}
        </Stack>
      )}
    </Box>
  );
}

export default function StockLevelWidget(): DashboardWidgetProps {
  return {
    label: 'dash-stock-level',
    title: t`Stock Level`,
    description: t`Parts with low or critical stock levels`,
    minWidth: 4,
    minHeight: 4,
    render: () => <StockLevelContent />
  };
}
