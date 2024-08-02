import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { formatCurrency } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import {
  DateColumn,
  LinkColumn,
  NoteColumn,
  PartColumn,
  ReferenceColumn,
  StatusColumn
} from '../ColumnRenderers';
import { StatusFilterOptions, TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export default function ReturnOrderLineItemTable({
  orderId
}: {
  orderId: number;
}) {
  const table = useTable('return-order-line-item');
  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        title: t`Part`,
        switchable: false,
        render: (record: any) => PartColumn(record?.part_detail)
      },
      {
        accessor: 'item',
        title: t`Stock Item`,
        switchable: false
      },
      ReferenceColumn({}),
      StatusColumn({
        model: ModelType.returnorderlineitem,
        sortable: true,
        accessor: 'outcome'
      }),
      {
        accessor: 'price',
        render: (record: any) =>
          formatCurrency(record.price, { currency: record.price_currency })
      },
      DateColumn({
        accessor: 'target_date'
      }),
      DateColumn({
        accessor: 'received_date'
      }),
      NoteColumn({
        accessor: 'notes'
      }),
      LinkColumn({})
    ];
  }, []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'received',
        label: t`Received`,
        description: t`Show items which have been received`
      },
      {
        name: 'status',
        label: t`Status`,
        description: t`Filter by line item status`,
        choiceFunction: StatusFilterOptions(ModelType.returnorderlineitem)
      }
    ];
  }, []);

  return (
    <>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.return_order_line_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            order: orderId,
            part_detail: true,
            item_detail: true,
            order_detail: true
          },
          tableFilters: tableFilters
        }}
      />
    </>
  );
}
