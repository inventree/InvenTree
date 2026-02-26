import { t } from '@lingui/core/macro';
import { IconSquareArrowRight } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { ActionButton } from '@lib/components/ActionButton';
import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { formatCurrency } from '../../defaults/formatters';
import {
  useReceiveReturnOrderLineItems,
  useReturnOrderLineItemFields
} from '../../forms/ReturnOrderForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  DateColumn,
  DescriptionColumn,
  LinkColumn,
  NoteColumn,
  PartColumn,
  ProjectCodeColumn,
  ReferenceColumn,
  StatusColumn,
  StockColumn
} from '../ColumnRenderers';
import { StatusFilterOptions } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export default function ReturnOrderLineItemTable({
  orderId,
  order,
  orderDetailRefresh,
  customerId,
  editable,
  currency
}: Readonly<{
  orderId: number;
  order: any;
  orderDetailRefresh: () => void;
  customerId: number;
  editable: boolean;
  currency: string;
}>) {
  const table = useTable('return-order-line-item');
  const user = useUserState();

  const roStatus = useStatusCodes({ modelType: ModelType.returnorder });

  const [selectedLine, setSelectedLine] = useState<number>(0);

  const inProgress: boolean = useMemo(() => {
    return order.status == roStatus.IN_PROGRESS;
  }, [order, roStatus]);

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
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const editLine = useEditApiFormModal({
    url: ApiEndpoints.return_order_line_list,
    pk: selectedLine,
    title: t`Edit Line Item`,
    fields: editLineFields,
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const deleteLine = useDeleteApiFormModal({
    url: ApiEndpoints.return_order_line_list,
    pk: selectedLine,
    title: t`Delete Line Item`,
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({
        part: 'part_detail',
        ordering: 'part'
      }),
      {
        accessor: 'part_detail.IPN',
        sortable: true,
        ordering: 'IPN'
      },
      DescriptionColumn({
        accessor: 'part_detail.description'
      }),
      StockColumn({
        accessor: 'item_detail',
        switchable: false,
        sortable: true,
        ordering: 'stock'
      }),
      StatusColumn({
        model: ModelType.stockitem,
        sortable: false,
        accessor: 'item_detail.status',
        title: t`Status`
      }),
      ReferenceColumn({}),
      ProjectCodeColumn({}),
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
        key='add-line-item'
        tooltip={t`Add Line Item`}
        hidden={!editable || !user.hasAddRole(UserRoles.return_order)}
        onClick={() => {
          newLine.open();
        }}
      />,
      <ActionButton
        key='receive-items'
        tooltip={t`Receive selected items`}
        icon={<IconSquareArrowRight />}
        hidden={
          !editable || inProgress || !user.hasChangeRole(UserRoles.return_order)
        }
        onClick={() => {
          setSelectedItems(
            table.selectedRecords.filter((record: any) => !record.received_date)
          );
          receiveLineItems.open();
        }}
        disabled={table.selectedRecords.length == 0}
      />
    ];
  }, [user, editable, inProgress, orderId, table.selectedRecords]);

  const [selectedItems, setSelectedItems] = useState<any[]>([]);

  const receiveLineItems = useReceiveReturnOrderLineItems({
    orderId: orderId,
    items: selectedItems,
    onFormSuccess: (data: any) => table.refreshTable()
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const received: boolean = !!record?.received_date;

      return [
        {
          hidden:
            received ||
            !editable ||
            !inProgress ||
            !user.hasChangeRole(UserRoles.return_order),
          title: t`Receive Item`,
          icon: <IconSquareArrowRight />,
          onClick: () => {
            setSelectedItems([record]);
            receiveLineItems.open();
          }
        },
        RowEditAction({
          hidden: !editable || !user.hasChangeRole(UserRoles.return_order),
          onClick: () => {
            setSelectedLine(record.pk);
            editLine.open();
          }
        }),
        RowDeleteAction({
          hidden: !editable || !user.hasDeleteRole(UserRoles.return_order),
          onClick: () => {
            setSelectedLine(record.pk);
            deleteLine.open();
          }
        })
      ];
    },
    [user, editable, inProgress]
  );

  return (
    <>
      {newLine.modal}
      {editLine.modal}
      {deleteLine.modal}
      {receiveLineItems.modal}
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
          enableSelection:
            inProgress && user.hasChangeRole(UserRoles.return_order),
          tableActions: tableActions,
          tableFilters: tableFilters,
          rowActions: rowActions,
          modelField: 'item',
          modelType: ModelType.stockitem
        }}
      />
    </>
  );
}
