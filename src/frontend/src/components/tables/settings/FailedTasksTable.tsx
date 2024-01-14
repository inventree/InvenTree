import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

export default function FailedTasksTable() {
  const table = useTable('tasks-failed');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'func',
        title: t`Task`,
        sortable: true
      },
      {
        accessor: 'started',
        title: t`Started`,
        sortable: true
      },
      {
        accessor: 'stopped',
        title: t`Stopped`,
        sortable: true
      },
      {
        accessor: 'attempt_count',
        title: t`Attempts`
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.task_failed_list)}
      tableState={table}
      columns={columns}
      props={{}}
    />
  );
}
