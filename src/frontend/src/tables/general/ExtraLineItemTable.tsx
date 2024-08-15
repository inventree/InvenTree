import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { formatCurrency } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { LinkColumn, NoteColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export default function ExtraLineItemTable({
  endpoint,
  orderId,
  role
}: {
  endpoint: ApiEndpoints;
  orderId: number;
  role: UserRoles;
}) {
  const table = useTable('extra-line-item');
  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'reference',
        switchable: false
      },
      {
        accessor: 'description'
      },
      {
        accessor: 'quantity',
        switchable: false
      },
      {
        accessor: 'unit_price',
        title: t`Unit Price`,
        render: (record: any) =>
          formatCurrency(record.unit_price, {
            currency: record.unit_price_currency
          })
      },
      {
        accessor: 'total_price',
        title: t`Total Price`,
        render: (record: any) =>
          formatCurrency(record.total_price, {
            currency: record.total_price_currency,
            multiplier: record.quantity
          })
      },
      NoteColumn({
        accessor: 'notes'
      }),
      LinkColumn({
        accessor: 'link'
      })
    ];
  }, []);

  return (
    <>
      <InvenTreeTable
        tableState={table}
        url={apiUrl(endpoint)}
        columns={tableColumns}
        props={{
          params: {
            order: orderId
          }
        }}
      />
    </>
  );
}
