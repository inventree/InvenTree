import { t } from '@lingui/macro';
import {
  ActionIcon,
  Alert,
  Center,
  Divider,
  Drawer,
  Group,
  Loader,
  LoadingOverlay,
  Space,
  Stack,
  Text,
  Tooltip
} from '@mantine/core';
import { IconBellCheck, IconBellPlus } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';

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
        .get(apiUrl(ApiEndpoints.notifications_list), {
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

  const hasNotifications: boolean = useMemo(() => {
    return (notificationQuery.data?.results?.length ?? 0) > 0;
  }, [notificationQuery.data]);

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
        <Group justify="space-between" wrap="nowrap">
          <StylishText size="lg">{t`Notifications`}</StylishText>
          <ActionIcon
            onClick={() => {
              onClose();
              navigate('/notifications/unread');
            }}
            variant="transparent"
          >
            <IconBellPlus />
          </ActionIcon>
        </Group>
      }
    >
      <Stack gap="xs">
        <Divider />
        {!hasNotifications && (
          <Alert color="green">
            <Text size="sm">{t`You have no unread notifications.`}</Text>
          </Alert>
        )}
        {hasNotifications &&
          notificationQuery.data?.results?.map((notification: any) => (
            <Group justify="space-between" key={notification.pk}>
              <Stack gap="3">
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
        {notificationQuery.isFetching && (
          <Center>
            <Loader size="sm" />
          </Center>
        )}
      </Stack>
    </Drawer>
  );
}
