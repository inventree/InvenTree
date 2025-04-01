import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import { apiUrl } from '@lib/functions';
import { useTable } from '@lib/hooks';
import { ApiEndpoints } from '@lib/index';
import { useUserState } from '@lib/index';
import type { TableColumn } from '@lib/tables';
import { InvenTreeTable } from '../../../lib/tables/InvenTreeTable';

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
