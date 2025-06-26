import { t } from '@lingui/core/macro';
import { Group, Text } from '@mantine/core';
import { IconCircleCheck, IconCircleX } from '@tabler/icons-react';
import { useMemo } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { useTable } from '../../hooks/UseTable';
import type { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

export default function ScheduledTasksTable() {
  const table = useTable('tasks-scheduled');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Task`,
        sortable: true,
        switchable: false,
        render: (record: any) => {
          return record.name || record.task;
        }
      },
      {
        accessor: 'last_run',
        title: t`Last Run`,
        sortable: true,
        switchable: false,
        render: (record: any) => {
          if (!record.last_run) {
            return '-';
          }

          return (
            <Group justify='space-between'>
              <Text>{record.last_run}</Text>
              {record.success ? (
                <IconCircleCheck color='green' />
              ) : (
                <IconCircleX color='red' />
              )}
            </Group>
          );
        }
      },
      {
        accessor: 'next_run',
        title: t`Next Run`,
        sortable: true,
        switchable: false
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.task_scheduled_list)}
      tableState={table}
      columns={columns}
      props={{}}
    />
  );
}
