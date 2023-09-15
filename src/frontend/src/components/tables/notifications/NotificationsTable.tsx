import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction } from '../RowActions';

export function NotificationTable({
  params,
  refreshId,
  tableKey,
  actions
}: {
  params: any;
  refreshId: string;
  tableKey: string;
  actions: (record: any) => RowAction[];
}) {
  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'age_human',
        title: t`Age`,
        sortable: true
      },
      {
        accessor: 'category',
        title: t`Category`,
        sortable: true
      },
      {
        accessor: `name`,
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
      url="/notifications/"
      tableKey={tableKey}
      refreshId={refreshId}
      params={params}
      rowActions={actions}
      columns={columns}
    />
  );
}
