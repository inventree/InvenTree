import { Trans, t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import { IconBellCheck, IconBellExclamation } from '@tabler/icons-react';
import { useMemo } from 'react';

import { api } from '../App';
import { StylishText } from '../components/items/StylishText';
import { PanelGroup } from '../components/nav/PanelGroup';
import { TableColumn } from '../components/tables/Column';
import { InvenTreeTable } from '../components/tables/InvenTreeTable';
import { RowAction } from '../components/tables/RowActions';
import { useTableRefresh } from '../hooks/TableRefresh';

function NotificationTable({
  params,
  refreshId,
  tableKey,
  actions
}: {
  params: any;
  refreshId: string;
  tableKey: string;
  actions: (record: any) => RowAction[];
}) {
  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'age_human',
        title: t`Age`,
        sortable: true
      },
      {
        accessor: 'category',
        title: t`Category`,
        sortable: true
      },
      {
        accessor: `name`,
        title: t`Notification`
      },
      {
        accessor: 'message',
        title: t`Message`
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url="/notifications/"
      tableKey={tableKey}
      refreshId={refreshId}
      params={params}
      rowActions={actions}
      columns={columns}
    />
  );
}

export default function NotificationsPage() {
  const unreadRefresh = useTableRefresh();
  const historyRefresh = useTableRefresh();

  const notificationPanels = useMemo(() => {
    return [
      {
        name: 'notifications-unread',
        label: t`Notifications`,
        icon: <IconBellExclamation size="18" />,
        content: (
          <NotificationTable
            params={{ read: false }}
            refreshId={unreadRefresh.refreshId}
            tableKey="notifications-unread"
            actions={(record) => [
              {
                title: t`Mark as read`,
                onClick: () => {
                  api
                    .patch(`/notifications/${record.pk}/`, {
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
            refreshId={historyRefresh.refreshId}
            tableKey="notifications-history"
            actions={(record) => [
              {
                title: t`Mark as unread`,
                onClick: () => {
                  api
                    .patch(`/notifications/${record.pk}/`, {
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
      <Stack spacing="xs">
        <StylishText>{t`Notifications`}</StylishText>
        <PanelGroup panels={notificationPanels} />
      </Stack>
    </>
  );
}
