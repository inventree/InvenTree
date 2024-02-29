import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { IconSquareArrowRight } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ActionButton } from '../../components/buttons/ActionButton';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import { Thumbnail } from '../../components/images/Thumbnail';
import { ProgressBar } from '../../components/items/ProgressBar';
import { RenderStockLocation } from '../../components/render/Stock';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import {
  usePurchaseOrderLineItemFields,
  useReceiveLineItems
} from '../../forms/PurchaseOrderForms';
import { getDetailUrl } from '../../functions/urls';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import {
  CurrencyColumn,
  LinkColumn,
  ReferenceColumn,
  TargetDateColumn,
  TotalPriceColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import {
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction
} from '../RowActions';
import { TableHoverCard } from '../TableHoverCard';

/*
 * Display a table of purchase order line items, for a specific order
 */
export function PurchaseOrderLineItemTable({
  orderId,
  params
}: {
  orderId: number;
  params?: any;
}) {
  const table = useTable('purchase-order-line-item');

  const navigate = useNavigate();
  const user = useUserState();

  const receiveLineItems = useReceiveLineItems({
    items: table.selectedRecords,
    orderPk: orderId
  });

  const tableColumns = useMemo(() => {
    return [
      {
        accessor: 'part',
        title: t`Part`,
        sortable: true,
        switchable: false,
        render: (record: any) => {
          return (
            <Thumbnail
              text={record?.part_detail?.name}
              src={record?.part_detail?.thumbnail ?? record?.part_detail?.image}
            />
          );
        }
      },
      {
        accessor: 'description',
        title: t`Part Description`,

        sortable: false,
        render: (record: any) => record?.part_detail?.description
      },
      ReferenceColumn(),
      {
        accessor: 'quantity',
        title: t`Quantity`,
        sortable: true,
        switchable: false,
        render: (record: any) => {
          let supplier_part = record?.supplier_part_detail ?? {};
          let part = record?.part_detail ?? supplier_part?.part_detail ?? {};
          let extra = [];

          if (supplier_part.pack_quantity_native != 1) {
            let total = record.quantity * supplier_part.pack_quantity_native;

            extra.push(
              <Text key="pack-quantity">
                {t`Pack Quantity`}: {supplier_part.pack_quantity}
              </Text>
            );

            extra.push(
              <Text key="total-quantity">
                {t`Total Quantity`}: {total} {part?.units}
              </Text>
            );
          }

          return (
            <TableHoverCard
              value={record.quantity}
              extra={extra}
              title={t`Quantity`}
            />
          );
        }
      },
      {
        accessor: 'received',
        title: t`Received`,
        sortable: false,

        render: (record: any) => (
          <ProgressBar
            progressLabel={true}
            value={record.received}
            maximum={record.quantity}
          />
        )
      },
      {
        accessor: 'pack_quantity',
        sortable: false,
        title: t`Pack Quantity`,
        render: (record: any) => record?.supplier_part_detail?.pack_quantity
      },
      {
        accessor: 'SKU',
        title: t`Supplier Code`,
        switchable: false,
        sortable: true,
        render: (record: any) => record?.supplier_part_detail?.SKU
      },
      {
        accessor: 'supplier_link',
        title: t`Supplier Link`,

        sortable: false,
        render: (record: any) => record?.supplier_part_detail?.link
      },
      {
        accessor: 'MPN',
        title: t`Manufacturer Code`,
        sortable: true,

        render: (record: any) =>
          record?.supplier_part_detail?.manufacturer_part_detail?.MPN
      },
      CurrencyColumn({
        accessor: 'purchase_price',
        title: t`Unit Price`
      }),
      TotalPriceColumn(),
      TargetDateColumn(),
      {
        accessor: 'destination',
        title: t`Destination`,
        sortable: false,
        render: (record: any) =>
          record.destination
            ? RenderStockLocation({ instance: record.destination_detail })
            : '-'
      },
      {
        accessor: 'notes',
        title: t`Notes`
      },
      LinkColumn()
    ];
  }, [orderId, user]);

  const newLine = useCreateApiFormModal({
    url: ApiEndpoints.purchase_order_line_list,
    title: t`Add Line Item`,
    fields: usePurchaseOrderLineItemFields({ create: true }),
    initialData: {
      order: orderId
    },
    onFormSuccess: table.refreshTable
  });

  const [selectedLine, setSelectedLine] = useState<number | undefined>(
    undefined
  );

  const editLine = useEditApiFormModal({
    url: ApiEndpoints.purchase_order_line_list,
    pk: selectedLine,
    title: t`Edit Line Item`,
    fields: usePurchaseOrderLineItemFields({}),
    onFormSuccess: table.refreshTable
  });

  const deleteLine = useDeleteApiFormModal({
    url: ApiEndpoints.purchase_order_line_list,
    pk: selectedLine,
    title: t`Delete Line Item`,
    onFormSuccess: table.refreshTable
  });

  const rowActions = useCallback(
    (record: any) => {
      let received = (record?.received ?? 0) >= (record?.quantity ?? 0);

      return [
        {
          hidden: received,
          title: t`Receive line item`,
          icon: <IconSquareArrowRight />,
          color: 'green'
        },
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedLine(record.pk);
            editLine.open();
          }
        }),
        RowDuplicateAction({
          hidden: !user.hasAddRole(UserRoles.purchase_order)
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedLine(record.pk);
            deleteLine.open();
          }
        })
      ];
    },
    [orderId, user]
  );

  // Custom table actions
  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key="add-line-item"
        tooltip={t`Add line item`}
        onClick={() => newLine.open()}
        hidden={!user?.hasAddRole(UserRoles.purchase_order)}
      />,
      <ActionButton
        key="receive-items"
        text={t`Receive items`}
        icon={<IconSquareArrowRight />}
        onClick={() => receiveLineItems.open()}
      />
    ];
  }, [orderId, user]);

  return (
    <>
      {receiveLineItems.modal}
      {newLine.modal}
      {editLine.modal}
      {deleteLine.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.purchase_order_line_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableSelection: true,
          enableDownload: true,
          params: {
            ...params,
            order: orderId,
            part_detail: true
          },
          rowActions: rowActions,
          tableActions: tableActions,
          onRowClick: (row: any) => {
            if (row.part) {
              navigate(getDetailUrl(ModelType.supplierpart, row.part));
            }
          }
        }}
      />
    </>
  );
}
