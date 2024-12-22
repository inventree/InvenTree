import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import type { TableState } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import type { TableColumn } from '../Column';
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
        params: params
      }}
    />
  );
}
