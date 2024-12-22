import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
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

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.task_pending_list)}
      tableState={table}
      columns={columns}
      props={{
        afterBulkDelete: onRecordsUpdated,
        enableBulkDelete: user.isStaff(),
        enableSelection: true
      }}
    />
  );
}
