import { t } from '@lingui/macro';
import { IconSquareArrowRight } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { ActionButton } from '../../components/buttons/ActionButton';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import { formatCurrency } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
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
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import {
  DateColumn,
  LinkColumn,
  NoteColumn,
  PartColumn,
  ReferenceColumn,
  StatusColumn
} from '../ColumnRenderers';
import { StatusFilterOptions, type TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

export default function ReturnOrderLineItemTable({
  orderId,
  order,
  customerId,
  currency
}: Readonly<{
  orderId: number;
  order: any;
  customerId: number;
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
        render: (record: any) => PartColumn({ part: record?.part_detail })
      },
      {
        accessor: 'part_detail.IPN',
        sortable: false
      },
      {
        accessor: 'part_detail.description',
        sortable: false
      },
      {
        accessor: 'item_detail.serial',
        title: t`Quantity`,
        switchable: false,
        render: (record: any) => {
          if (record.item_detail.serial && record.quantity == 1) {
            return `# ${record.item_detail.serial}`;
          } else {
            return record.quantity;
          }
        }
      },
      StatusColumn({
        model: ModelType.stockitem,
        sortable: false,
        accessor: 'item_detail.status',
        title: t`Status`
      }),
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
        key='add-line-item'
        tooltip={t`Add Line Item`}
        hidden={!user.hasAddRole(UserRoles.return_order)}
        onClick={() => {
          newLine.open();
        }}
      />,
      <ActionButton
        key='receive-items'
        tooltip={t`Receive selected items`}
        icon={<IconSquareArrowRight />}
        hidden={!inProgress || !user.hasChangeRole(UserRoles.return_order)}
        onClick={() => {
          setSelectedItems(
            table.selectedRecords.filter((record: any) => !record.received_date)
          );
          receiveLineItems.open();
        }}
        disabled={table.selectedRecords.length == 0}
      />
    ];
  }, [user, inProgress, orderId, table.selectedRecords]);

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
    [user, inProgress]
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
