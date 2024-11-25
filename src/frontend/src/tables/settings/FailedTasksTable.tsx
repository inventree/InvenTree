import { t } from '@lingui/macro';
import { Drawer, Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { hideNotification, showNotification } from '@mantine/notifications';
import { IconExclamationCircle } from '@tabler/icons-react';
import { useMemo, useState } from 'react';

import { StylishText } from '../../components/items/StylishText';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

export default function FailedTasksTable({
  onRecordsUpdated
}: Readonly<{
  onRecordsUpdated: () => void;
}>) {
  const table = useTable('tasks-failed');
  const user = useUserState();

  const [error, setError] = useState<string>('');

  const [opened, { open, close }] = useDisclosure(false);

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'func',
        title: t`Task`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'pk',
        title: t`Task ID`
      },
      {
        accessor: 'started',
        title: t`Started`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'stopped',
        title: t`Stopped`,
        sortable: true,
        switchable: false
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
        size='xl'
        position='right'
        title={<StylishText>{t`Error Details`}</StylishText>}
        onClose={close}
      >
        {error.split('\n').map((line: string, index: number) => {
          return (
            <Text key={`error-${index}`} size='sm'>
              {line}
            </Text>
          );
        })}
      </Drawer>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.task_failed_list)}
        tableState={table}
        columns={columns}
        props={{
          enableBulkDelete: user.isStaff(),
          afterBulkDelete: onRecordsUpdated,
          enableSelection: true,
          onRowClick: (row: any) => {
            if (row.result) {
              setError(row.result);
              open();
            } else {
              hideNotification('failed-task');
              showNotification({
                id: 'failed-task',
                title: t`No Information`,
                message: t`No error details are available for this task`,
                color: 'red',
                icon: <IconExclamationCircle />
              });
            }
          }
        }}
      />
    </>
  );
}
