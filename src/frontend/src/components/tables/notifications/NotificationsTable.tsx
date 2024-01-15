import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { TableState } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction } from '../RowActions';

export function NotificationTable({
  params,
  tableState,
  actions
}: {
  params: any;
  tableState: TableState;
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
      url={apiUrl(ApiPaths.notifications_list)}
      tableState={tableState}
      columns={columns}
      props={{
        rowActions: actions,
        enableSelection: true,
        params: params
      }}
    />
  );
}
