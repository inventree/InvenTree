import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { TableState } from '@lib/types/Tables';
import type { TableColumn } from '@lib/types/Tables';
import { InvenTreeTable } from '../InvenTreeTable';
import type { RowAction } from '../RowActions';

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
