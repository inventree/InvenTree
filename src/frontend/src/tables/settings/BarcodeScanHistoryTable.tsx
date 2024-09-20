import { t } from '@lingui/macro';
import { Badge, Group, Text } from '@mantine/core';
import { useMemo } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useUserFilters } from '../../hooks/UseFilter';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

/*
 * Display the barcode scan history table
 */
export default function BarcodeScanHistoryTable() {
  const user = useUserState();
  const table = useTable('barcode-history');

  const userFilters = useUserFilters();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'timestamp',
        sortable: true,
        switchable: false,
        render: (record: any) => {
          return (
            <Group justify="space-between">
              <Text>{record.timestamp}</Text>
              {record.user_detail && (
                <Badge size="xs">{record.user_detail.username}</Badge>
              )}
            </Group>
          );
        }
      },
      {
        accessor: 'data',
        sortable: true,
        switchable: false
      },
      {
        accessor: 'endpoint',
        sortable: true
      },
      {
        accessor: 'status',
        sortable: true
      }
    ];
  }, []);

  const filters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'user',
        label: t`User`,
        choices: userFilters.choices,
        description: t`Filter by user`
      }
    ];
  }, [userFilters]);

  return (
    <>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.barcode_history)}
        tableState={table}
        columns={tableColumns}
        props={{
          tableFilters: filters
        }}
      />
    </>
  );
}
