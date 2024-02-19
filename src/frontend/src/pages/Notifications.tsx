import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import { modals } from '@mantine/modals';
import {
  IconBellCheck,
  IconBellExclamation,
  IconCircleCheck,
  IconCircleX,
  IconMailOpened,
  IconTrash
} from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';

import { api } from '../App';
import { ActionButton } from '../components/buttons/ActionButton';
import { PageDetail } from '../components/nav/PageDetail';
import { PanelGroup } from '../components/nav/PanelGroup';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { useTable } from '../hooks/UseTable';
import { apiUrl } from '../states/ApiState';
import { NotificationTable } from '../tables/notifications/NotificationsTable';

export default function NotificationsPage() {
  const unreadTable = useTable('unreadnotifications');
  const readTable = useTable('readnotifications');

  const markAllAsRead = useCallback(() => {
    api
      .get(apiUrl(ApiEndpoints.notifications_readall), {
        params: {
          read: false
        }
      })
      .then((_response) => {
        unreadTable.refreshTable();
        readTable.refreshTable();
      })
      .catch((_error) => {});
  }, []);

  const deleteNotifications = useCallback(() => {
    modals.openConfirmModal({
      title: t`Delete Notifications`,
      onConfirm: () => {
        api
          .delete(apiUrl(ApiEndpoints.notifications_list), {
            data: {
              filters: {
                read: true
              }
            }
          })
          .then((_response) => {
            readTable.refreshTable();
          })
          .catch((_error) => {});
      }
    });
  }, []);

  const notificationPanels = useMemo(() => {
    return [
      {
        name: 'unread',
        label: t`Notifications`,
        icon: <IconBellExclamation size="18" />,
        content: (
          <NotificationTable
            params={{ read: false }}
            tableState={unreadTable}
            actions={(record) => [
              {
                title: t`Mark as read`,
                color: 'green',
                icon: <IconCircleCheck />,
                onClick: () => {
                  let url = apiUrl(ApiEndpoints.notifications_list, record.pk);
                  api
                    .patch(url, {
                      read: true
                    })
                    .then((response) => {
                      unreadTable.refreshTable();
                    });
                }
              }
            ]}
            tableActions={[
              <ActionButton
                icon={<IconMailOpened />}
                tooltip={`Mark all as read`}
                onClick={markAllAsRead}
              />
            ]}
          />
        )
      },
      {
        name: 'history',
        label: t`History`,
        icon: <IconBellCheck size="18" />,
        content: (
          <NotificationTable
            params={{ read: true }}
            tableState={readTable}
            actions={(record) => [
              {
                title: t`Mark as unread`,
                icon: <IconCircleX />,
                onClick: () => {
                  let url = apiUrl(ApiEndpoints.notifications_list, record.pk);

                  api
                    .patch(url, {
                      read: false
                    })
                    .then((response) => {
                      readTable.refreshTable();
                    });
                }
              },
              {
                title: t`Delete`,
                color: 'red',
                icon: <IconTrash />,
                onClick: () => {
                  api
                    .delete(apiUrl(ApiEndpoints.notifications_list, record.pk))
                    .then((response) => {
                      readTable.refreshTable();
                    });
                }
              }
            ]}
            tableActions={[
              <ActionButton
                color="red"
                icon={<IconTrash />}
                tooltip={`Delete notifications`}
                onClick={deleteNotifications}
              />
            ]}
          />
        )
      }
    ];
  }, [unreadTable, readTable]);

  return (
    <>
      <Stack>
        <PageDetail title={t`Notifications`} />
        <PanelGroup pageKey="notifications" panels={notificationPanels} />
      </Stack>
    </>
  );
}
