import { t } from '@lingui/macro';
import { Drawer, Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useMemo, useState } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { StylishText } from '../../items/StylishText';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

export default function FailedTasksTable() {
  const table = useTable('tasks-failed');

  const [error, setError] = useState<string>('');

  const [opened, { open, close }] = useDisclosure(false);

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'func',
        title: t`Task`,
        sortable: true
      },
      {
        accessor: 'id',
        title: t`Task ID`
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
    <>
      <Drawer
        opened={opened}
        size="xl"
        position="right"
        title={<StylishText>{t`Error Details`}</StylishText>}
        onClose={close}
      >
        {error.split('\n').map((line: string) => {
          return <Text size="sm">{line}</Text>;
        })}
      </Drawer>
      <InvenTreeTable
        url={apiUrl(ApiPaths.task_failed_list)}
        tableState={table}
        columns={columns}
        props={{
          onRowClick: (row: any) => {
            setError(row.result);
            open();
          }
        }}
      />
    </>
  );
}
