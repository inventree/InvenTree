import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { useMemo } from 'react';

import { RenderUser } from '../../components/render/User';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { DateColumn, DescriptionColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export function StockTrackingTable({ itemId }: { itemId: number }) {
  const table = useTable('stock_tracking');
  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      DateColumn({
        switchable: false
      }),
      DescriptionColumn({
        accessor: 'label'
      }),
      {
        accessor: 'details',
        title: t`Details`,
        switchable: false
      },
      {
        accessor: 'user',
        title: t`User`,
        render: (record: any) => {
          if (!record.user_detail) {
            return <Text size="sm" fs="italic">{t`No user information`}</Text>;
          }

          return RenderUser({ instance: record.user_detail });
        }
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      tableState={table}
      url={apiUrl(ApiEndpoints.stock_tracking_list)}
      columns={tableColumns}
      props={{
        params: {
          item: itemId,
          user_detail: true
        }
      }}
    />
  );
}
