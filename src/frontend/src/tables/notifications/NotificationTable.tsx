import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { ApiEndpoints } from '@lib/core';
import type { RowAction, TableColumn } from '@lib/tables';
import type { TableState } from '../../../lib/hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { InvenTreeTable } from '../InvenTreeTable';

export function NotificationTable({
  params,
  tableState,
  tableActions,
  actions
}: Readonly<{
  params: any;
  tableState: TableState;
  tableActions: any[];
  actions: (record: any) => RowAction[];
}>) {
  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'age_human',
        title: t`Age`,
        sortable: true,
        ordering: 'creation'
      },
      {
        accessor: 'category',
        title: t`Category`,
        sortable: true
      },
      {
        accessor: 'name',
        title: t`Notification`
      },
      {
        accessor: 'message',
        title: t`Message`
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.notifications_list)}
      tableState={tableState}
      columns={columns}
      props={{
        rowActions: actions,
        tableActions: tableActions,
        enableSelection: true,
        enableBulkDelete: true,
        params: params
      }}
    />
  );
}
