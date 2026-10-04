import { t } from '@lingui/core/macro';
import {
  Avatar,
  Box,
  Center,
  Group,
  Loader,
  ScrollArea,
  Stack,
  Text,
  ThemeIcon,
  Timeline,
  useMantineColorScheme
} from '@mantine/core';
import { useDocumentVisibility } from '@mantine/hooks';
import {
  IconBell,
  IconCheck,
  IconAlertTriangle
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { formatDistanceToNow } from 'date-fns';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { useApi } from '../../../contexts/ApiContext';
import type { DashboardWidgetProps } from '../DashboardWidget';

function getNotifIcon(category: string) {
  if (category?.includes('error') || category?.includes('alert')) {
    return { icon: <IconAlertTriangle size={14} />, color: 'orange' };
  }
  if (category?.includes('success') || category?.includes('complete')) {
    return { icon: <IconCheck size={14} />, color: 'teal' };
  }
  return { icon: <IconBell size={14} />, color: 'blue' };
}

function AccessLogsContent() {
  const api = useApi();
  const visibility = useDocumentVisibility();
  const { colorScheme } = useMantineColorScheme();
  const isDark = colorScheme === 'dark';

  const query = useQuery({
    queryKey: ['dashboard-access-logs', visibility],
    enabled: visibility === 'visible',
    staleTime: 2 * 60 * 1000,
    refetchInterval: 5 * 60 * 1000,
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.notifications_list), {
          params: {
            limit: 12,
            ordering: '-creation_date'
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

  const notifications = query.data ?? [];

  return (
    <Box style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Group justify='space-between' mb='md'>
        <Text fw={700} size='md'>
          {t`Access Logs`}
        </Text>
        <Text size='xs' c='dimmed'>
          {t`Recent system activity`}
        </Text>
      </Group>

      {notifications.length === 0 ? (
        <Center style={{ flex: 1 }}>
          <Stack align='center' gap='xs'>
            <ThemeIcon size='xl' radius='xl' variant='light' color='blue'>
              <IconBell size={20} />
            </ThemeIcon>
            <Text size='sm' c='dimmed'>
              {t`No recent activity`}
            </Text>
          </Stack>
        </Center>
      ) : (
        <ScrollArea style={{ flex: 1 }} scrollbarSize={4}>
          <Timeline
            bulletSize={28}
            lineWidth={1}
            color='blue'
            active={notifications.length}
          >
            {notifications.map((notif: any) => {
              const { icon, color } = getNotifIcon(notif.category ?? '');
              const timeAgo = notif.creation_date
                ? formatDistanceToNow(new Date(notif.creation_date), {
                    addSuffix: true
                  })
                : '';

              return (
                <Timeline.Item
                  key={notif.pk}
                  bullet={
                    <ThemeIcon
                      size={24}
                      radius='xl'
                      color={notif.read ? 'gray' : color}
                      variant='light'
                    >
                      {icon}
                    </ThemeIcon>
                  }
                  title={
                    <Text
                      size='xs'
                      fw={notif.read ? 400 : 700}
                      c={notif.read ? 'dimmed' : undefined}
                    >
                      {notif.message ?? notif.name ?? t`Notification`}
                    </Text>
                  }
                >
                  <Group gap='xs' mt={2} wrap='nowrap'>
                    {notif.actor && (
                      <Text size='xs' c='dimmed' truncate style={{ maxWidth: 120 }}>
                        {notif.actor}
                      </Text>
                    )}
                    <Text size='xs' c='dimmed'>
                      {timeAgo}
                    </Text>
                  </Group>
                </Timeline.Item>
              );
            })}
          </Timeline>
        </ScrollArea>
      )}
    </Box>
  );
}

export default function AccessLogsWidget(): DashboardWidgetProps {
  return {
    label: 'dash-access-logs',
    title: t`Access Logs`,
    description: t`Recent system notifications and activity`,
    minWidth: 3,
    minHeight: 4,
    render: () => <AccessLogsContent />
  };
}
