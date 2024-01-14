import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

export default function ScheduledTasksTable() {
  const table = useTable('tasks-scheduled');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'func',
        title: t`Task`
      },
      {
        accessor: 'next_run',
        title: t`Scheduled`
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.task_scheduled_list)}
      tableState={table}
      columns={columns}
      props={{}}
    />
  );
}
