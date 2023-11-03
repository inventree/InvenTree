import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { IconSquareArrowRight } from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';

import { ProgressBar } from '../../../components/items/ProgressBar';
import { purchaseOrderLineItemFields } from '../../../forms/PurchaseOrderForms';
import { openCreateApiForm, openEditApiForm } from '../../../functions/forms';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { ActionButton } from '../../buttons/ActionButton';
import { AddItemButton } from '../../buttons/AddItemButton';
import { Thumbnail } from '../../images/Thumbnail';
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
  const { tableKey, refreshTable } = useTableRefresh(
    'purchase-order-line-item'
  );

  const user = useUserState();

  const rowActions = useCallback(
    (record: any) => {
      // TODO: Hide certain actions if user does not have required permissions

      let received = (record?.received ?? 0) >= (record?.quantity ?? 0);

      return [
        {
          hidden: received,
          title: t`Receive`,
          tooltip: t`Receive line item`,
          color: 'green'
        },
        RowEditAction({
          onClick: () => {
            let supplier = record?.supplier_part_detail?.supplier;

            if (!supplier) {
              return;
            }

            let fields = purchaseOrderLineItemFields({
              supplierId: supplier
            });

            openEditApiForm({
              url: ApiPaths.purchase_order_line_list,
              pk: record.pk,
              title: t`Edit Line Item`,
              fields: fields,
              onFormSuccess: refreshTable,
              successMessage: t`Line item updated`
            });
          }
        }),
        RowDuplicateAction({}),
        RowDeleteAction({})
      ];
    },
    [orderId, user]
  );

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
      {
        accessor: 'reference',
        title: t`Reference`,
        sortable: true
      },
      {
        accessor: 'quantity',
        title: t`Quantity`,
        sortable: true,
        switchable: false,
        render: (record: any) => {
          let part = record?.part_detail;
          let supplier_part = record?.supplier_part_detail ?? {};
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
                {t`Total Quantity`}: {total}
                {part.units}
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
        sortable: true
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

      {
        accessor: 'purchase_price',
        title: t`Unit Price`,
        sortable: true

        // TODO: custom renderer
      },
      {
        accessor: 'total_price',
        title: t`Total Price`,
        sortable: true

        // TODO: custom renderer
      },
      {
        accessor: 'target_date',
        title: t`Target Date`,
        sortable: true
      },
      {
        accessor: 'destination',
        title: t`Destination`,
        sortable: false

        // TODO: Custom renderer
      },
      {
        accessor: 'notes',
        title: t`Notes`
      },
      {
        accessor: 'link',
        title: t`Link`

        // TODO: custom renderer
      }
    ];
  }, [orderId, user]);

  const addLine = useCallback(() => {
    openCreateApiForm({
      url: ApiPaths.purchase_order_line_list,
      title: t`Add Line Item`,
      fields: purchaseOrderLineItemFields({}),
      onFormSuccess: refreshTable,
      successMessage: t`Line item added`
    });
  }, []);

  // Custom table actions
  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        tooltip={t`Add line item`}
        onClick={addLine}
        hidden={!user?.checkUserRole('purchaseorder', 'add')}
      />,
      <ActionButton text={t`Receive items`} icon={<IconSquareArrowRight />} />
    ];
  }, [orderId, user]);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.purchase_order_line_list)}
      tableKey={tableKey}
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
        customActionGroups: tableActions
      }}
    />
  );
}
