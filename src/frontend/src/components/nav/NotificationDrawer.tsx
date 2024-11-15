import { t } from '@lingui/macro';
import {
  ActionIcon,
  Alert,
  Anchor,
  Center,
  Divider,
  Drawer,
  Group,
  Loader,
  Paper,
  Stack,
  Text,
  Tooltip
} from '@mantine/core';
import { IconArrowRight, IconBellCheck } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import type { ModelType } from '../../enums/ModelType';
import { navigateToLink } from '../../functions/navigation';
import { getDetailUrl } from '../../functions/urls';
import { base_url } from '../../main';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { Boundary } from '../Boundary';
import { StylishText } from '../items/StylishText';
import { ModelInformationDict } from '../render/ModelType';

/**
 * Render a single notification entry in the drawer
 */
function NotificationEntry({
  notification,
  onRead
}: Readonly<{
  notification: any;
  onRead: () => void;
}>) {
  const navigate = useNavigate();

  let link = notification.target?.link;

  const model_type = notification.target?.model_type;
  const model_id = notification.target?.model_id;

  // If a valid model type is provided, that overrides the specified link
  if (model_type as ModelType) {
    const model_info = ModelInformationDict[model_type as ModelType];
    if (model_info?.url_detail && model_id) {
      link = getDetailUrl(model_type as ModelType, model_id);
    } else if (model_info?.url_overview) {
      link = model_info.url_overview;
    }
  }

  return (
    <Paper p='xs' shadow='xs'>
      <Group justify='space-between' wrap='nowrap'>
        <Tooltip
          label={notification.message}
          position='bottom-end'
          hidden={!notification.message}
        >
          <Stack gap={2}>
            <Anchor
              href={link ? `/${base_url}${link}` : '#'}
              underline='hover'
              target='_blank'
              onClick={(event: any) => {
                if (link) {
                  // Mark the notification as read
                  onRead();
                }

                if (link.startsWith('/')) {
                  navigateToLink(link, navigate, event);
                }
              }}
            >
              <Text size='sm'>{notification.name}</Text>
            </Anchor>
            <Text size='xs'>{notification.age_human}</Text>
          </Stack>
        </Tooltip>
        <Tooltip label={t`Mark as read`} position='bottom-end'>
          <ActionIcon variant='transparent' onClick={onRead}>
            <IconBellCheck />
          </ActionIcon>
        </Tooltip>
      </Group>
    </Paper>
  );
}

/**
 * Construct a notification drawer.
 */
export function NotificationDrawer({
  opened,
  onClose
}: Readonly<{
  opened: boolean;
  onClose: () => void;
}>) {
  const { isLoggedIn } = useUserState();

  const navigate = useNavigate();

  const notificationQuery = useQuery({
    enabled: opened && isLoggedIn(),
    queryKey: ['notifications', opened],
    queryFn: async () =>
      api
        .get(apiUrl(ApiEndpoints.notifications_list), {
          params: {
            read: false,
            limit: 10,
            ordering: '-creation'
          }
        })
        .then((response) => response.data)
        .catch((error) => {
          return error;
        }),
    refetchOnMount: false
  });

  const hasNotifications: boolean = useMemo(() => {
    return (notificationQuery.data?.results?.length ?? 0) > 0;
  }, [notificationQuery.data]);

  const markAllAsRead = useCallback(() => {
    api
      .get(apiUrl(ApiEndpoints.notifications_readall), {
        params: {
          read: false
        }
      })
      .catch((_error) => {})
      .then((_response) => {
        notificationQuery.refetch();
      });
  }, []);

  const markAsRead = useCallback((notification: any) => {
    api
      .patch(apiUrl(ApiEndpoints.notifications_list, notification.pk), {
        read: true
      })
      .then(() => {
        notificationQuery.refetch();
      })
      .catch(() => {
        notificationQuery.refetch();
      });
  }, []);

  return (
    <Drawer
      opened={opened}
      size='md'
      position='right'
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
        <Group justify='space-between' wrap='nowrap'>
          <StylishText size='lg'>{t`Notifications`}</StylishText>
          <Group justify='end' wrap='nowrap'>
            <Tooltip label={t`Mark all as read`}>
              <ActionIcon
                variant='transparent'
                onClick={() => {
                  markAllAsRead();
                }}
              >
                <IconBellCheck />
              </ActionIcon>
            </Tooltip>
            <Tooltip label={t`View all notifications`}>
              <ActionIcon
                onClick={(event: any) => {
                  onClose();
                  navigateToLink('/notifications/unread', navigate, event);
                }}
                variant='transparent'
              >
                <IconArrowRight />
              </ActionIcon>
            </Tooltip>
          </Group>
        </Group>
      }
    >
      <Boundary label='NotificationDrawer'>
        <Stack gap='xs'>
          <Divider />
          {!hasNotifications && (
            <Alert color='green'>
              <Text size='sm'>{t`You have no unread notifications.`}</Text>
            </Alert>
          )}
          {hasNotifications &&
            notificationQuery.data?.results?.map((notification: any) => (
              <NotificationEntry
                key={`notification-${notification.pk}`}
                notification={notification}
                onRead={() => markAsRead(notification)}
              />
            ))}
          {notificationQuery.isFetching && (
            <Center>
              <Loader size='sm' />
            </Center>
          )}
        </Stack>
      </Boundary>
    </Drawer>
  );
}
