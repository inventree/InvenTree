import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

export default function PendingTasksTable() {
  const table = useTable('tasks-pending');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'func',
        title: t`Task`
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
        sortable: true
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.task_pending_list)}
      tableState={table}
      columns={columns}
      props={{}}
    />
  );
}
