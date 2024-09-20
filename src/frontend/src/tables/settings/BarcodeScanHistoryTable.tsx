import { t } from '@lingui/macro';
import { Badge, Group, Text } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { useUserFilters } from '../../hooks/UseFilter';
import { useDeleteApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction } from '../RowActions';

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
            <Group justify="space-between" wrap="nowrap">
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
        switchable: true,
        render: (record: any) => {
          return (
            <Text size="xs" style={{ textWrap: 'wrap', lineBreak: 'auto' }}>
              {record.data}
            </Text>
          );
        }
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

  const canDelete: boolean = useMemo(() => {
    return user.isStaff() && user.hasDeleteRole(UserRoles.admin);
  }, [user]);

  const [selectedResult, setSelectedResult] = useState<number>(0);

  const deleteResult = useDeleteApiFormModal({
    url: ApiEndpoints.barcode_history,
    pk: selectedResult,
    title: t`Delete Barcode Scan Record`,
    table: table
  });

  const rowActions = useCallback(
    (record: any) => {
      return [
        RowDeleteAction({
          hidden: !canDelete,
          onClick: () => {
            setSelectedResult(record.pk);
            deleteResult.open();
          }
        })
      ];
    },
    [canDelete, user]
  );

  return (
    <>
      {deleteResult.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.barcode_history)}
        tableState={table}
        columns={tableColumns}
        props={{
          tableFilters: filters,
          enableBulkDelete: canDelete,
          rowActions: rowActions
        }}
      />
    </>
  );
}
