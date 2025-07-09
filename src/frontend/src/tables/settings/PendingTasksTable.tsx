import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableColumn } from '@lib/types/Tables';
import { notifications, showNotification } from '@mantine/notifications';
import { IconTrashXFilled, IconX } from '@tabler/icons-react';
import { api } from '../../App';
import { ActionButton } from '../../components/buttons/ActionButton';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { InvenTreeTable } from '../InvenTreeTable';

export default function PendingTasksTable({
  onRecordsUpdated
}: Readonly<{
  onRecordsUpdated: () => void;
}>) {
  const table = useTable('tasks-pending');
  const user = useUserState();

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'func',
        title: t`Task`,
        switchable: false
      },
      {
        accessor: 'task_id',
        title: t`Task ID`
      },
      {
        accessor: 'name',
        title: t`Name`
      },
      {
        accessor: 'lock',
        title: t`Created`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'args',
        title: t`Arguments`
      },
      {
        accessor: 'kwargs',
        title: t`Keywords`
      }
    ];
  }, []);

  const tableActions = useMemo(() => {
    return [
      <ActionButton
        key='remove-all'
        icon={<IconTrashXFilled />}
        tooltip={t`Remove all pending tasks`}
        onClick={() => {
          api
            .delete(`${apiUrl(ApiEndpoints.task_pending_list)}?all=true`)
            .then(() => {
              notifications.show({
                id: 'notes',
                title: t`Success`,
                message: t`All pending tasks deleted`,
                color: 'green'
              });
              table.refreshTable();
            })
            .catch((err) => {
              showNotification({
                title: t`Error while deleting all pending tasks`,
                message:
                  err.response.data?.non_field_errors ??
                  err.message ??
                  t`Unknown error`,
                color: 'red',
                icon: <IconX />
              });
            });
        }}
        hidden={!user.hasAddRole(UserRoles.admin)}
      />
    ];
  }, [user]);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.task_pending_list)}
      tableState={table}
      columns={columns}
      props={{
        afterBulkDelete: onRecordsUpdated,
        enableBulkDelete: user.isStaff(),
        enableSelection: true,
        tableActions: tableActions
      }}
    />
  );
}
