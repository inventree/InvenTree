import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/buttons/AddItemButton';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '@lib/forms';
import { apiUrl } from '@lib/functions';
import { formatCurrency } from '@lib/functions';
import { useTable } from '@lib/hooks';
import type { ApiEndpoints } from '@lib/index';
import type { UserRoles } from '@lib/index';
import { useUserState } from '@lib/index';
import type { RowAction, TableColumn } from '@lib/tables';
import {
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction
} from '@lib/tables';
import { InvenTreeTable } from '../../../lib/tables/InvenTreeTable';
import { extraLineItemFields } from '../../forms/CommonForms';
import { LinkColumn, NoteColumn } from '../ColumnRenderers';

export default function ExtraLineItemTable({
  endpoint,
  orderId,
  currency,
  role
}: Readonly<{
  endpoint: ApiEndpoints;
  orderId: number;
  currency: string;
  role: UserRoles;
}>) {
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
        accessor: 'price',
        title: t`Unit Price`,
        render: (record: any) =>
          formatCurrency(record.price, {
            currency: record.price_currency
          })
      },
      {
        accessor: 'total_price',
        title: t`Total Price`,
        render: (record: any) =>
          formatCurrency(record.price, {
            currency: record.price_currency,
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

  const [initialData, setInitialData] = useState<any>({});

  const [selectedLine, setSelectedLine] = useState<number>(0);

  const newLineItem = useCreateApiFormModal({
    url: endpoint,
    title: t`Add Line Item`,
    fields: extraLineItemFields(),
    initialData: {
      ...initialData,
      price_currency: currency
    },
    table: table
  });

  const editLineItem = useEditApiFormModal({
    url: endpoint,
    pk: selectedLine,
    title: t`Edit Line Item`,
    fields: extraLineItemFields(),
    table: table
  });

  const deleteLineItem = useDeleteApiFormModal({
    url: endpoint,
    pk: selectedLine,
    title: t`Delete Line Item`,
    table: table
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(role),
          onClick: () => {
            setSelectedLine(record.pk);
            editLineItem.open();
          }
        }),
        RowDuplicateAction({
          hidden: !user.hasAddRole(role),
          onClick: () => {
            setInitialData({ ...record });
            newLineItem.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(role),
          onClick: () => {
            setSelectedLine(record.pk);
            deleteLineItem.open();
          }
        })
      ];
    },
    [user, role]
  );

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-line-item'
        tooltip={t`Add Extra Line Item`}
        hidden={!user.hasAddRole(role)}
        onClick={() => {
          setInitialData({
            order: orderId
          });
          newLineItem.open();
        }}
      />
    ];
  }, [user, role]);

  return (
    <>
      {newLineItem.modal}
      {editLineItem.modal}
      {deleteLineItem.modal}
      <InvenTreeTable
        tableState={table}
        url={apiUrl(endpoint)}
        columns={tableColumns}
        props={{
          params: {
            order: orderId
          },
          rowActions: rowActions,
          tableActions: tableActions
        }}
      />
    </>
  );
}
