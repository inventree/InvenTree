import { t } from '@lingui/core/macro';
import { IconFlag, IconSquareArrowRight } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { ActionButton } from '@lib/components/ActionButton';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { Alert } from '@mantine/core';
import { LineItemCreationMenu } from '../../components/items/LineItemCreationMenu';
import {
  DateColumn,
  DescriptionColumn,
  LineItemColumn,
  LinkColumn,
  NoteColumn,
  PartColumn,
  PercentageColumn,
  ProjectCodeColumn,
  ReferenceColumn,
  StatusColumn,
  StockColumn
} from '../../components/tables/ColumnRenderers';
import { StatusFilterOptions } from '../../components/tables/Filter';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { formatCurrency } from '../../defaults/formatters';
import { dataImporterSessionFields } from '../../forms/ImporterForms';
import {
  useReceiveReturnOrderLineItems,
  useReturnOrderLineItemFields
} from '../../forms/ReturnOrderForms';
import {
  useBulkEditApiFormModal,
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { useImporterState } from '../../states/ImporterState';
import { useUserState } from '../../states/UserState';

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
  const openImporter = useImporterState((state) => state.openImporter);

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

  const importSessionFields = useMemo(() => {
    const fields = dataImporterSessionFields({
      modelType: ModelType.returnorderlineitem
    });

    fields.field_overrides.value = {
      order: orderId
    };

    fields.field_defaults.value = {
      price_currency: currency
    };

    return fields;
  }, [orderId, currency]);

  const importLineItems = useCreateApiFormModal({
    url: ApiEndpoints.import_session_list,
    title: t`Import Line Items`,
    fields: importSessionFields,
    onFormSuccess: (response: any) => {
      openImporter(response.pk, {
        onClose: table.refreshTable
      });
    }
  });

  const setOutcome = useBulkEditApiFormModal({
    url: ApiEndpoints.return_order_line_list,
    items: table.selectedIds,
    title: t`Set Outcome`,
    preFormContent: (
      <Alert color='blue'>
        {t`Adjust the outcome for the selected line items.`}
      </Alert>
    ),
    fields: {
      outcome: {}
    },
    onFormSuccess: table.refreshTable
  });

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      LineItemColumn({}),
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
      PercentageColumn({
        accessor: 'discount',
        title: t`Discount`,
        defaultVisible: false
      }),
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
      <LineItemCreationMenu
        key='add-line-item-actions'
        tooltip={t`Add Line Item`}
        addLabel={t`Add Line Item`}
        importLabel={t`Import Line Items`}
        hidden={!editable || !user.hasAddRole(UserRoles.return_order)}
        onAdd={() => {
          newLine.open();
        }}
        onImport={() => importLineItems.open()}
      />,
      <ActionButton
        key='receive-items'
        tooltip={t`Receive selected items`}
        icon={<IconSquareArrowRight />}
        hidden={
          !editable ||
          !inProgress ||
          !user.hasChangeRole(UserRoles.return_order)
        }
        onClick={() => {
          setSelectedItems(
            table.selectedRecords.filter((record: any) => !record.received_date)
          );
          receiveLineItems.open();
        }}
        disabled={table.selectedRecords.length == 0}
      />,
      <ActionButton
        key='set-outcome'
        tooltip={t`Set outcome for selected items`}
        icon={<IconFlag />}
        hidden={!editable || !user.hasChangeRole(UserRoles.return_order)}
        onClick={() => {
          setOutcome.open();
        }}
        disabled={table.selectedRecords.length == 0}
      />
    ];
  }, [
    user,
    editable,
    inProgress,
    orderId,
    table.selectedRecords,
    importLineItems
  ]);

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
      {setOutcome.modal}
      {importLineItems.modal}
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
          defaultSortColumn: 'line',
          enableSelection:
            editable && user.hasChangeRole(UserRoles.return_order),
          enableBulkDelete:
            editable && user.hasDeleteRole(UserRoles.return_order),
          afterBulkDelete: orderDetailRefresh,
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
