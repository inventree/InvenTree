import { t } from '@lingui/macro';
import { useCallback, useMemo } from 'react';

import { purchaseOrderLineItemFields } from '../../../forms/PurchaseOrderForms';
import { openCreateApiForm, openEditApiForm } from '../../../functions/forms';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { AddItemButton } from '../../buttons/AddItemButton';
import { Thumbnail } from '../../images/Thumbnail';
import { InvenTreeTable } from '../InvenTreeTable';
import {
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction
} from '../RowActions';

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

      return [
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
        switchable: true,
        sortable: false,
        render: (record: any) => record?.part_detail?.description
      },
      {
        accessor: 'reference',
        title: t`Reference`,
        sortable: true,
        switchable: true
      },
      {
        accessor: 'quantity',
        title: t`Quantity`,
        sortable: true,
        switchable: false
        // TODO: custom quantity renderer
      },
      {
        accessor: 'recevied',
        title: t`Received`,
        sortable: false,
        switchable: true
        // TODO: custom renderer
      },
      {
        accessor: 'pack_quantity',
        sortable: false,
        switchable: true,
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
        switchable: true,
        sortable: false,
        render: (record: any) => record?.supplier_part_detail?.link
      },
      {
        accessor: 'MPN',
        title: t`Manufacturer Code`,
        sortable: true,
        switchable: true,
        render: (record: any) =>
          record?.supplier_part_detail?.manufacturer_part_detail?.MPN
      },

      {
        accessor: 'purchase_price',
        title: t`Unit Price`,
        sortable: true,
        switchable: true
        // TODO: custom renderer
      },
      {
        accessor: 'total_price',
        title: t`Total Price`,
        sortable: true,
        switchable: true
        // TODO: custom renderer
      },
      {
        accessor: 'target_date',
        title: t`Target Date`,
        sortable: true,
        switchable: true
      },
      {
        accessor: 'destination',
        title: t`Destination`,
        sortable: false,
        switchable: true
        // TODO: Custom renderer
      },
      {
        accessor: 'notes',
        title: t`Notes`,
        switchable: true
      },
      {
        accessor: 'link',
        title: t`Link`,
        switchable: true
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
    let actions = [];

    // TODO: Hide "add item" if order is not active

    if (user?.checkUserRole('purchaseorder', 'add')) {
      actions.push(
        <AddItemButton tooltip={t`Add line item`} callback={addLine} />
      );
    }

    return actions;
  }, [orderId, user]);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.purchase_order_line_list)}
      tableKey={tableKey}
      columns={tableColumns}
      props={{
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
