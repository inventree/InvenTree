import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import { IconBellCheck, IconBellExclamation } from '@tabler/icons-react';
import { useMemo } from 'react';

import { api } from '../App';
import { StylishText } from '../components/items/StylishText';
import { PageDetail } from '../components/nav/PageDetail';
import { PanelGroup } from '../components/nav/PanelGroup';
import { NotificationTable } from '../components/tables/notifications/NotificationsTable';
import { useTableRefresh } from '../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../states/ApiState';

export default function NotificationsPage() {
  const unreadRefresh = useTableRefresh('unreadnotifications');
  const historyRefresh = useTableRefresh('readnotifications');

  const notificationPanels = useMemo(() => {
    return [
      {
        name: 'notifications-unread',
        label: t`Notifications`,
        icon: <IconBellExclamation size="18" />,
        content: (
          <NotificationTable
            params={{ read: false }}
            tableKey={unreadRefresh.tableKey}
            actions={(record) => [
              {
                title: t`Mark as read`,
                onClick: () => {
                  let url = apiUrl(ApiPaths.notifications_list, record.pk);
                  api
                    .patch(url, {
                      read: true
                    })
                    .then((response) => {
                      unreadRefresh.refreshTable();
                    });
                }
              }
            ]}
          />
        )
      },
      {
        name: 'notifications-history',
        label: t`History`,
        icon: <IconBellCheck size="18" />,
        content: (
          <NotificationTable
            params={{ read: true }}
            tableKey={historyRefresh.tableKey}
            actions={(record) => [
              {
                title: t`Mark as unread`,
                onClick: () => {
                  let url = apiUrl(ApiPaths.notifications_list, record.pk);

                  api
                    .patch(url, {
                      read: false
                    })
                    .then((response) => {
                      historyRefresh.refreshTable();
                    });
                }
              },
              {
                title: t`Delete`,
                color: 'red',
                onClick: () => {
                  api
                    .delete(`/notifications/${record.pk}/`)
                    .then((response) => {
                      historyRefresh.refreshTable();
                    });
                }
              }
            ]}
          />
        )
      }
    ];
  }, [historyRefresh, unreadRefresh]);

  return (
    <>
      <Stack>
        <PageDetail title={t`Notifications`} />
        <PanelGroup pageKey="notifications" panels={notificationPanels} />
      </Stack>
    </>
  );
}
