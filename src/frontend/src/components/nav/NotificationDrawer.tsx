import { t } from '@lingui/macro';
import {
  ActionIcon,
  Drawer,
  LoadingOverlay,
  Space,
  Tooltip
} from '@mantine/core';
import { Badge, Group, Stack, Text } from '@mantine/core';
import { IconBookmark } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../App';

/**
 * Construct a notification drawer.
 */
export function NotificationDrawer({
  opened,
  onClose
}: {
  opened: boolean;
  onClose: () => void;
}) {
  const notificationQuery = useQuery({
    enabled: opened,
    queryKey: ['notifications', opened],
    queryFn: async () =>
      api
        .get('/notifications/', {
          params: {
            read: false,
            limit: 10
          }
        })
        .then((response) => response.data)
        .catch((error) => {
          console.error('Error fetching notifications:', error);
          return error;
        }),
    refetchOnMount: false,
    refetchOnWindowFocus: false
  });

  return (
    <Drawer
      opened={opened}
      size="md"
      position="right"
      onClose={onClose}
      withCloseButton={true}
      styles={{
        header: {
          width: '100%'
        },
        title: {
          width: '100%'
        }
      }}
      title={
        <Group position="apart" noWrap={true}>
          <Text size="lg">{t`Notifications`}</Text>
        </Group>
      }
    >
      <Stack>
        <LoadingOverlay visible={notificationQuery.isFetching} />
        {notificationQuery.data?.results.map((notification: any) => (
          <Group position="apart">
            <Stack spacing="xs">
              <Text size="sm">{notification.target?.name ?? 'target'}</Text>
              <Text size="xs">{notification.age_human ?? 'name'}</Text>
            </Stack>
            <Space />
            <ActionIcon
              color="gray"
              variant="hover"
              onClick={() => {
                api
                  .patch(`/notifications/${notification.pk}/`, {
                    read: true
                  })
                  .then((response) => {
                    notificationQuery.refetch();
                  });
              }}
            >
              <Tooltip label={t`Mark as read`}>
                <IconBookmark />
              </Tooltip>
            </ActionIcon>
          </Group>
        ))}
      </Stack>
    </Drawer>
  );
}
