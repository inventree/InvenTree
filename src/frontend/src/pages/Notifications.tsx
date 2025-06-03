import { t } from '@lingui/core/macro';
import { Stack } from '@mantine/core';
import {
  IconBellCheck,
  IconBellExclamation,
  IconCircleCheck,
  IconMail,
  IconMailOpened,
  IconTrash
} from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { useNavigate } from 'react-router-dom';
import { ActionButton } from '../components/buttons/ActionButton';
import { PageDetail } from '../components/nav/PageDetail';
import { PanelGroup } from '../components/panels/PanelGroup';
import { useApi } from '../contexts/ApiContext';
import { useTable } from '../hooks/UseTable';
import { useGlobalSettingsState } from '../states/SettingsState';
import { NotificationTable } from '../tables/notifications/NotificationTable';

export default function NotificationsPage() {
  const api = useApi();
  const navigate = useNavigate();
  const globalSettings = useGlobalSettingsState();
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

  const notificationPanels = useMemo(() => {
    return [
      {
        name: 'unread',
        label: t`Notifications`,
        icon: <IconBellExclamation size='18' />,
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
                  const url = apiUrl(
                    ApiEndpoints.notifications_list,
                    record.pk
                  );
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
                tooltip={t`Mark all as read`}
                onClick={markAllAsRead}
              />
            ]}
          />
        )
      },
      {
        name: 'history',
        label: t`History`,
        icon: <IconBellCheck size='18' />,
        content: (
          <NotificationTable
            params={{ read: true }}
            tableState={readTable}
            actions={(record) => [
              {
                title: t`Mark as unread`,
                icon: <IconMail />,
                onClick: () => {
                  const url = apiUrl(
                    ApiEndpoints.notifications_list,
                    record.pk
                  );

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
            tableActions={[]}
          />
        )
      }
    ];
  }, [unreadTable, readTable]);

  if (!globalSettings.isSet('NOTIFICATIONS_ENABLE')) {
    // Redirect to the dashboard if notifications are not enabled
    navigate('/');
  }

  return (
    <Stack>
      <PageDetail title={t`Notifications`} />
      <PanelGroup pageKey='notifications' panels={notificationPanels} />
    </Stack>
  );
}
