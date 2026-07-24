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
import useTable from '@lib/hooks/UseTable';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';
import {
  DescriptionColumn,
  PartColumn
} from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { useRepairOrderLineItemFields } from '../../forms/RepairOrderForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { useUserState } from '../../states/UserState';

export default function RepairOrderLineItemTable({
  orderId,
  order,
  orderDetailRefresh,
  editable
}: Readonly<{
  orderId: number;
  order: any;
  orderDetailRefresh: () => void;
  editable: boolean;
}>) {
  const table = useTable('repair-order-line-item');
  const user = useUserState();

  const roStatus = useStatusCodes({ modelType: ModelType.repairorder });

  const [selectedLine, setSelectedLine] = useState<number>(0);

  const inProgress: boolean = useMemo(() => {
    return (
      order.status == roStatus.PENDING || order.status == roStatus.IN_PROGRESS
    );
  }, [order, roStatus]);

  const newLineFields = useRepairOrderLineItemFields({
    orderId: orderId,
    create: true
  });

  const editLineFields = useRepairOrderLineItemFields({
    orderId: orderId
  });

  const newLine = useCreateApiFormModal({
    url: ApiEndpoints.repair_order_line_list,
    title: t`Add Line Item`,
    fields: newLineFields,
    initialData: {
      order: orderId
    },
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const editLine = useEditApiFormModal({
    url: ApiEndpoints.repair_order_line_list,
    pk: selectedLine,
    title: t`Edit Line Item`,
    fields: editLineFields,
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const deleteLine = useDeleteApiFormModal({
    url: ApiEndpoints.repair_order_line_list,
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
      DescriptionColumn({
        accessor: 'part_detail.description'
      }),
      {
        accessor: 'quantity',
        title: t`Quantity`,
        sortable: true
      }
    ];
  }, []);

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-line-item'
        tooltip={t`Add Line Item`}
        hidden={!editable || !user.hasAddRole(UserRoles.repair_order)}
        onClick={() => {
          newLine.open();
        }}
      />
    ];
  }, [user, editable]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !editable || !user.hasChangeRole(UserRoles.repair_order),
          onClick: () => {
            setSelectedLine(record.pk);
            editLine.open();
          }
        }),
        RowDeleteAction({
          hidden: !editable || !user.hasDeleteRole(UserRoles.repair_order),
          onClick: () => {
            setSelectedLine(record.pk);
            deleteLine.open();
          }
        })
      ];
    },
    [user, editable]
  );

  return (
    <>
      {newLine.modal}
      {editLine.modal}
      {deleteLine.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.repair_order_line_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            order: orderId,
            part_detail: true
          },
          tableActions: tableActions,
          rowActions: rowActions,
          modelType: ModelType.repairorderlineitem
        }}
      />
    </>
  );
}
