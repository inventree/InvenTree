import { t } from '@lingui/macro';
import {
  ActionIcon,
  Alert,
  Divider,
  Drawer,
  LoadingOverlay,
  Space,
  Tooltip
} from '@mantine/core';
import { Group, Stack, Text } from '@mantine/core';
import { IconBellCheck, IconBellPlus } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';
import { StylishText } from '../items/StylishText';

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
  const navigate = useNavigate();

  const notificationQuery = useQuery({
    enabled: opened,
    queryKey: ['notifications', opened],
    queryFn: async () =>
      api
        .get(ApiEndpoints.notifications_list, {
          params: {
            read: false,
            limit: 10
          }
        })
        .then((response) => response.data)
        .catch((error) => {
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
      withCloseButton={false}
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
          <StylishText size="lg">{t`Notifications`}</StylishText>
          <ActionIcon
            onClick={() => {
              onClose();
              navigate('/notifications/unread');
            }}
          >
            <IconBellPlus />
          </ActionIcon>
        </Group>
      }
    >
      <Stack spacing="xs">
        <Divider />
        <LoadingOverlay visible={notificationQuery.isFetching} />
        {(notificationQuery.data?.results?.length ?? 0) == 0 && (
          <Alert color="green">
            <Text size="sm">{t`You have no unread notifications.`}</Text>
          </Alert>
        )}
        {notificationQuery.data?.results?.map((notification: any) => (
          <Group position="apart" key={notification.pk}>
            <Stack spacing="3">
              {notification?.target?.link ? (
                <Text
                  size="sm"
                  component={Link}
                  to={notification?.target?.link}
                  target="_blank"
                >
                  {notification.target?.name ??
                    notification.name ??
                    t`Notification`}
                </Text>
              ) : (
                <Text size="sm">
                  {notification.target?.name ??
                    notification.name ??
                    t`Notification`}
                </Text>
              )}
              <Text size="xs">{notification.age_human ?? ''}</Text>
            </Stack>
            <Space />
            <ActionIcon
              color="gray"
              variant="hover"
              onClick={() => {
                let url = apiUrl(
                  ApiEndpoints.notifications_list,
                  notification.pk
                );
                api
                  .patch(url, {
                    read: true
                  })
                  .then((response) => {
                    notificationQuery.refetch();
                  });
              }}
            >
              <Tooltip label={t`Mark as read`}>
                <IconBellCheck />
              </Tooltip>
            </ActionIcon>
          </Group>
        ))}
      </Stack>
    </Drawer>
  );
}
