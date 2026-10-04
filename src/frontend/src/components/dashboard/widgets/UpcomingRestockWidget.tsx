import { t } from '@lingui/core/macro';
import {
  Anchor,
  Avatar,
  Box,
  Center,
  Group,
  Loader,
  Stack,
  Table,
  Text,
  useMantineColorScheme
} from '@mantine/core';
import { useDocumentVisibility } from '@mantine/hooks';
import { IconBox } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { navigateToLink } from '@lib/functions/Navigation';
import { useApi } from '../../../contexts/ApiContext';
import type { DashboardWidgetProps } from '../DashboardWidget';

function UpcomingRestockContent() {
  const api = useApi();
  const navigate = useNavigate();
  const visibility = useDocumentVisibility();
  const { colorScheme } = useMantineColorScheme();
  const isDark = colorScheme === 'dark';

  // Fetch active purchase order lines (incoming stock)
  const query = useQuery({
    queryKey: ['dashboard-upcoming-restock', visibility],
    enabled: visibility === 'visible',
    staleTime: 5 * 60 * 1000,
    refetchInterval: 10 * 60 * 1000,
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.purchase_order_line_list), {
          params: {
            order_outstanding: true,
            limit: 6,
            ordering: 'target_date'
          }
        })
        .then((res) => res.data?.results ?? [])
  });

  if (query.isLoading) {
    return (
      <Center style={{ height: '100%' }}>
        <Loader size='md' />
      </Center>
    );
  }

  const lines = query.data ?? [];

  return (
    <Box style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Group justify='space-between' mb='md'>
        <Text fw={700} size='md'>
          {t`Upcoming Restock`}
        </Text>
        <Anchor
          size='xs'
          fw={600}
          onClick={(e: any) =>
            navigateToLink('/purchasing', navigate, e)
          }
        >
          {lines.length > 0 ? `${t`View All`} (${lines.length})` : t`View All`}
        </Anchor>
      </Group>

      {lines.length === 0 ? (
        <Center style={{ flex: 1 }}>
          <Stack align='center' gap='xs'>
            <IconBox size={32} color={isDark ? '#555' : '#ccc'} />
            <Text size='sm' c='dimmed'>
              {t`No pending purchase order lines`}
            </Text>
          </Stack>
        </Center>
      ) : (
        <Box style={{ flex: 1, overflow: 'auto' }}>
          <Table highlightOnHover verticalSpacing='xs' withRowBorders={false}>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>
                  <Text size='xs' c='dimmed' fw={600} tt='uppercase'>
                    {t`Part`}
                  </Text>
                </Table.Th>
                <Table.Th>
                  <Text size='xs' c='dimmed' fw={600} tt='uppercase' ta='right'>
                    {t`Qty`}
                  </Text>
                </Table.Th>
                <Table.Th>
                  <Text size='xs' c='dimmed' fw={600} tt='uppercase' ta='right'>
                    {t`Due`}
                  </Text>
                </Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {lines.map((line: any) => {
                const partName =
                  line.part_detail?.full_name ??
                  line.part_detail?.name ??
                  `Part #${line.part}`;
                const targetDate = line.target_date
                  ? new Date(line.target_date).toLocaleDateString()
                  : '—';

                return (
                  <Table.Tr key={line.pk}>
                    <Table.Td>
                      <Group gap='xs' wrap='nowrap'>
                        <Avatar
                          src={line.part_detail?.thumbnail}
                          size='sm'
                          radius='sm'
                          color='blue'
                          variant='light'
                        >
                          <IconBox size={14} />
                        </Avatar>
                        <Anchor
                          size='xs'
                          fw={600}
                          truncate
                          style={{ maxWidth: 140 }}
                          onClick={(e: any) =>
                            navigateToLink(
                              `/purchasing/${line.order}`,
                              navigate,
                              e
                            )
                          }
                        >
                          {partName}
                        </Anchor>
                      </Group>
                    </Table.Td>
                    <Table.Td ta='right'>
                      <Text size='xs' fw={700}>
                        {(line.quantity ?? 0).toLocaleString()}
                      </Text>
                    </Table.Td>
                    <Table.Td ta='right'>
                      <Text size='xs' c='dimmed'>
                        {targetDate}
                      </Text>
                    </Table.Td>
                  </Table.Tr>
                );
              })}
            </Table.Tbody>
          </Table>
        </Box>
      )}
    </Box>
  );
}

export default function UpcomingRestockWidget(): DashboardWidgetProps {
  return {
    label: 'dash-restock',
    title: t`Upcoming Restock`,
    description: t`Purchase order lines with incoming stock`,
    minWidth: 4,
    minHeight: 4,
    render: () => <UpcomingRestockContent />
  };
}
