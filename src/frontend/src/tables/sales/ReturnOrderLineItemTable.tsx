import { t } from '@lingui/macro';
import { IconSquareArrowRight } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { formatCurrency } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useReturnOrderLineItemFields } from '../../forms/ReturnOrderForms';
import { notYetImplemented } from '../../functions/notifications';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
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
import { RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

export default function ReturnOrderLineItemTable({
  orderId,
  customerId,
  currency
}: {
  orderId: number;
  customerId: number;
  currency: string;
}) {
  const table = useTable('return-order-line-item');
  const user = useUserState();

  const [selectedLine, setSelectedLine] = useState<number>(0);

  const newLineFields = useReturnOrderLineItemFields({
    orderId: orderId,
    customerId: customerId,
    create: true
  });

  const editLineFields = useReturnOrderLineItemFields({
    orderId: orderId,
    customerId: customerId
  });

  const newLine = useCreateApiFormModal({
    url: ApiEndpoints.return_order_line_list,
    title: t`Add Line Item`,
    fields: newLineFields,
    initialData: {
      order: orderId,
      price_currency: currency
    },
    table: table
  });

  const editLine = useEditApiFormModal({
    url: ApiEndpoints.return_order_line_list,
    pk: selectedLine,
    title: t`Edit Line Item`,
    fields: editLineFields,
    table: table
  });

  const deleteLine = useDeleteApiFormModal({
    url: ApiEndpoints.return_order_line_list,
    pk: selectedLine,
    title: t`Delete Line Item`,
    table: table
  });

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
        accessor: 'target_date',
        title: t`Target Date`
      }),
      DateColumn({
        accessor: 'received_date',
        title: t`Received Date`
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

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        tooltip={t`Add line item`}
        hidden={!user.hasAddRole(UserRoles.return_order)}
        onClick={() => {
          newLine.open();
        }}
      />
    ];
  }, [user, orderId]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const received: boolean = !!record?.received_date;

      return [
        {
          hidden: received || !user.hasChangeRole(UserRoles.return_order),
          title: t`Receive Item`,
          icon: <IconSquareArrowRight />,
          onClick: notYetImplemented
        },
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.return_order),
          onClick: () => {
            setSelectedLine(record.pk);
            editLine.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.return_order),
          onClick: () => {
            setSelectedLine(record.pk);
            deleteLine.open();
          }
        })
      ];
    },
    [user]
  );

  return (
    <>
      {newLine.modal}
      {editLine.modal}
      {deleteLine.modal}
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
          tableActions: tableActions,
          tableFilters: tableFilters,
          rowActions: rowActions
        }}
      />
    </>
  );
}
