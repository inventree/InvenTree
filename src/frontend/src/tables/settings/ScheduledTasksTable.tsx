import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { IconCircleCheck, IconCircleX } from '@tabler/icons-react';
import { useMemo } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

export default function ScheduledTasksTable() {
  const table = useTable('tasks-scheduled');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'func',
        title: t`Task`,
        sortable: true,
        switchable: false
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
            <Group position="apart">
              <Text>{record.last_run}</Text>
              {record.success ? (
                <IconCircleCheck color="green" />
              ) : (
                <IconCircleX color="red" />
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
