import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction
} from '@lib/components/RowActions';
import type { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import type { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableColumn } from '@lib/types/Tables';
import { formatCurrency } from '../../defaults/formatters';
import { taxExtraLineItemFields } from '../../forms/CommonForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  CurrencyColumn,
  DecimalColumn,
  DescriptionColumn,
  LinkColumn,
  NoteColumn,
  PercentageColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export default function ExtraLineItemTable({
  endpoint,
  orderId,
  orderDetailRefresh,
  currency,
  role
}: Readonly<{
  endpoint: ApiEndpoints;
  orderId: number;
  orderDetailRefresh: () => void;
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
      DescriptionColumn({}),
      DecimalColumn({
        accessor: 'quantity',
        switchable: false
      }),
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
      CurrencyColumn({
        accessor: 'price_with_tax',
        title: t`Price with Tax`
      }),
      CurrencyColumn({
        accessor: 'subtotal',
        title: t`Subtotal`
      }),
      CurrencyColumn({
        accessor: 'tax_amount',
        title: t`Total Tax`
      }),
      CurrencyColumn({
        accessor: 'total_with_tax',
        title: t`Total with Tax`
      }),
      PercentageColumn({
        accessor: 'tax_rate',
        title: t`Tax Rate`,
        sortable: true
      }),
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
    fields: taxExtraLineItemFields({ create: true }),
    initialData: {
      ...initialData,
      price_currency: currency
    },
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const editLineItem = useEditApiFormModal({
    url: endpoint,
    pk: selectedLine,
    title: t`Edit Line Item`,
    fields: taxExtraLineItemFields({ create: false }),
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const deleteLineItem = useDeleteApiFormModal({
    url: endpoint,
    pk: selectedLine,
    title: t`Delete Line Item`,
    onFormSuccess: orderDetailRefresh,
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
