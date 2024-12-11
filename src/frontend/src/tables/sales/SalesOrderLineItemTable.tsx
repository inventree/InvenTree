import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import {
  IconArrowRight,
  IconHash,
  IconShoppingCart,
  IconSquareArrowRight,
  IconTools
} from '@tabler/icons-react';
import type { DataTableRowExpansionProps } from 'mantine-datatable';
import { type ReactNode, useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ActionButton } from '../../components/buttons/ActionButton';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ProgressBar } from '../../components/items/ProgressBar';
import OrderPartsWizard from '../../components/wizards/OrderPartsWizard';
import { formatCurrency } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useBuildOrderFields } from '../../forms/BuildForms';
import {
  useAllocateToSalesOrderForm,
  useSalesOrderAllocateSerialsFields,
  useSalesOrderLineItemFields
} from '../../forms/SalesOrderForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import { DateColumn, LinkColumn, PartColumn } from '../ColumnRenderers';
import type { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import {
  type RowAction,
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction,
  RowViewAction
} from '../RowActions';
import RowExpansionIcon from '../RowExpansionIcon';
import { TableHoverCard } from '../TableHoverCard';
import SalesOrderAllocationTable from './SalesOrderAllocationTable';

export default function SalesOrderLineItemTable({
  orderId,
  currency,
  customerId,
  editable
}: Readonly<{
  orderId: number;
  currency: string;
  customerId: number;
  editable: boolean;
}>) {
  const navigate = useNavigate();
  const user = useUserState();
  const table = useTable('sales-order-line-item');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        sortable: true,
        switchable: false,
        render: (record: any) => {
          return (
            <Group wrap='nowrap'>
              <RowExpansionIcon
                enabled={record.allocated}
                expanded={table.isRowExpanded(record.pk)}
              />
              <PartColumn part={record.part_detail} />
            </Group>
          );
        }
      },
      {
        accessor: 'part_detail.IPN',
        title: t`IPN`,
        switchable: true
      },
      {
        accessor: 'part_detail.description',
        title: t`Description`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'reference',
        sortable: false,
        switchable: true
      },
      {
        accessor: 'quantity',
        sortable: true
      },
      {
        accessor: 'sale_price',
        render: (record: any) =>
          formatCurrency(record.sale_price, {
            currency: record.sale_price_currency
          })
      },
      {
        accessor: 'total_price',
        title: t`Total Price`,
        render: (record: any) =>
          formatCurrency(record.sale_price, {
            currency: record.sale_price_currency,
            multiplier: record.quantity
          })
      },
      DateColumn({
        accessor: 'target_date',
        sortable: true,
        title: t`Target Date`
      }),
      {
        accessor: 'stock',
        title: t`Available Stock`,
        render: (record: any) => {
          const part_stock = record?.available_stock ?? 0;
          const variant_stock = record?.available_variant_stock ?? 0;
          const available = part_stock + variant_stock;

          const required = Math.max(
            record.quantity - record.allocated - record.shipped,
            0
          );

          let color: string | undefined = undefined;
          let text = `${available}`;

          const extra: ReactNode[] = [];

          if (available <= 0) {
            color = 'red';
            text = t`No stock available`;
          } else if (available < required) {
            color = 'orange';
          }

          if (variant_stock > 0) {
            extra.push(<Text size='sm'>{t`Includes variant stock`}</Text>);
          }

          if (record.building > 0) {
            extra.push(
              <Text size='sm'>
                {t`In production`}: {record.building}
              </Text>
            );
          }

          if (record.on_order > 0) {
            extra.push(
              <Text size='sm'>
                {t`On order`}: {record.on_order}
              </Text>
            );
          }

          return (
            <TableHoverCard
              value={<Text c={color}>{text}</Text>}
              extra={extra}
              title={t`Stock Information`}
            />
          );
        }
      },
      {
        accessor: 'allocated',
        sortable: true,
        render: (record: any) => (
          <ProgressBar
            progressLabel={true}
            value={record.allocated}
            maximum={record.quantity}
          />
        )
      },
      {
        accessor: 'shipped',
        sortable: true,
        render: (record: any) => (
          <ProgressBar
            progressLabel={true}
            value={record.shipped}
            maximum={record.quantity}
          />
        )
      },
      {
        accessor: 'notes'
      },
      LinkColumn({
        accessor: 'link'
      })
    ];
  }, [table.isRowExpanded]);

  const [selectedLine, setSelectedLine] = useState<number>(0);

  const [initialData, setInitialData] = useState({});

  const createLineFields = useSalesOrderLineItemFields({
    orderId: orderId,
    customerId: customerId,
    create: true
  });

  const newLine = useCreateApiFormModal({
    url: ApiEndpoints.sales_order_line_list,
    title: t`Add Line Item`,
    fields: createLineFields,
    initialData: {
      ...initialData,
      sale_price_currency: currency
    },
    table: table
  });

  const editLineFields = useSalesOrderLineItemFields({
    orderId: orderId,
    customerId: customerId,
    create: false
  });

  const editLine = useEditApiFormModal({
    url: ApiEndpoints.sales_order_line_list,
    pk: selectedLine,
    title: t`Edit Line Item`,
    fields: editLineFields,
    table: table
  });

  const deleteLine = useDeleteApiFormModal({
    url: ApiEndpoints.sales_order_line_list,
    pk: selectedLine,
    title: t`Delete Line Item`,
    table: table
  });

  const allocateSerialFields = useSalesOrderAllocateSerialsFields({
    itemId: selectedLine,
    orderId: orderId
  });

  const allocateBySerials = useCreateApiFormModal({
    url: ApiEndpoints.sales_order_allocate_serials,
    pk: orderId,
    title: t`Allocate Serial Numbers`,
    initialData: initialData,
    fields: allocateSerialFields,
    table: table
  });

  const buildOrderFields = useBuildOrderFields({ create: true });

  const newBuildOrder = useCreateApiFormModal({
    url: ApiEndpoints.build_order_list,
    title: t`Create Build Order`,
    fields: buildOrderFields,
    initialData: initialData,
    follow: true,
    modelType: ModelType.build
  });

  const [selectedItems, setSelectedItems] = useState<any[]>([]);

  const allocateStock = useAllocateToSalesOrderForm({
    orderId: orderId,
    lineItems: selectedItems,
    onFormSuccess: () => {
      table.refreshTable();
      table.clearSelectedRecords();
    }
  });

  const [partsToOrder, setPartsToOrder] = useState<any[]>([]);

  const orderPartsWizard = OrderPartsWizard({
    parts: partsToOrder
  });

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'allocated',
        label: t`Allocated`,
        description: t`Show lines which are fully allocated`
      },
      {
        name: 'completed',
        label: t`Completed`,
        description: t`Show lines which are completed`
      }
    ];
  }, []);

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-line-item'
        tooltip={t`Add Line Item`}
        onClick={() => {
          setInitialData({
            order: orderId
          });
          newLine.open();
        }}
        hidden={!editable || !user.hasAddRole(UserRoles.sales_order)}
      />,
      <ActionButton
        key='order-parts'
        hidden={!user.hasAddRole(UserRoles.purchase_order)}
        disabled={!table.hasSelectedRecords}
        tooltip={t`Order Parts`}
        icon={<IconShoppingCart />}
        color='blue'
        onClick={() => {
          setPartsToOrder(table.selectedRecords.map((r) => r.part_detail));
          orderPartsWizard.openWizard();
        }}
      />,
      <ActionButton
        key='allocate-stock'
        tooltip={t`Allocate Stock`}
        icon={<IconArrowRight />}
        disabled={!table.hasSelectedRecords}
        color='green'
        onClick={() => {
          setSelectedItems(
            table.selectedRecords.filter((r) => r.allocated < r.quantity)
          );
          allocateStock.open();
        }}
      />
    ];
  }, [user, orderId, table.hasSelectedRecords, table.selectedRecords]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const allocated = (record?.allocated ?? 0) > (record?.quantity ?? 0);

      return [
        RowViewAction({
          title: t`View Part`,
          modelType: ModelType.part,
          modelId: record.part,
          navigate: navigate,
          hidden: !user.hasViewRole(UserRoles.part)
        }),
        {
          hidden:
            allocated ||
            !editable ||
            !user.hasChangeRole(UserRoles.sales_order),
          title: t`Allocate Stock`,
          icon: <IconSquareArrowRight />,
          color: 'green',
          onClick: () => {
            setSelectedItems([record]);
            allocateStock.open();
          }
        },
        {
          hidden:
            !record?.part_detail?.trackable ||
            allocated ||
            !editable ||
            !user.hasChangeRole(UserRoles.sales_order),
          title: t`Allocate serials`,
          icon: <IconHash />,
          color: 'green',
          onClick: () => {
            setSelectedLine(record.pk);
            setInitialData({
              quantity: record.quantity - record.allocated
            });
            allocateBySerials.open();
          }
        },
        {
          hidden:
            allocated ||
            !user.hasAddRole(UserRoles.build) ||
            !record?.part_detail?.assembly,
          title: t`Build stock`,
          icon: <IconTools />,
          color: 'blue',
          onClick: () => {
            setInitialData({
              part: record.part,
              quantity: (record?.quantity ?? 1) - (record?.allocated ?? 0),
              sales_order: orderId
            });
            newBuildOrder.open();
          }
        },
        {
          hidden:
            allocated ||
            !user.hasAddRole(UserRoles.purchase_order) ||
            !record?.part_detail?.purchaseable,
          title: t`Order stock`,
          icon: <IconShoppingCart />,
          color: 'blue',
          onClick: () => {
            setPartsToOrder([record.part_detail]);
            orderPartsWizard.openWizard();
          }
        },
        RowEditAction({
          hidden: !editable || !user.hasChangeRole(UserRoles.sales_order),
          onClick: () => {
            setSelectedLine(record.pk);
            editLine.open();
          }
        }),
        RowDuplicateAction({
          hidden: !editable || !user.hasAddRole(UserRoles.sales_order),
          onClick: () => {
            setInitialData(record);
            newLine.open();
          }
        }),
        RowDeleteAction({
          hidden: !editable || !user.hasDeleteRole(UserRoles.sales_order),
          onClick: () => {
            setSelectedLine(record.pk);
            deleteLine.open();
          }
        })
      ];
    },
    [navigate, user, editable]
  );

  // Control row expansion
  const rowExpansion: DataTableRowExpansionProps<any> = useMemo(() => {
    return {
      allowMultiple: true,
      expandable: ({ record }: { record: any }) => {
        return table.isRowExpanded(record.pk) || record.allocated > 0;
      },
      content: ({ record }: { record: any }) => {
        return (
          <SalesOrderAllocationTable
            showOrderInfo={false}
            showPartInfo={false}
            orderId={orderId}
            lineItemId={record.pk}
            partId={record.part}
            allowEdit
            isSubTable
          />
        );
      }
    };
  }, [orderId, table.isRowExpanded]);

  return (
    <>
      {editLine.modal}
      {deleteLine.modal}
      {newLine.modal}
      {newBuildOrder.modal}
      {allocateBySerials.modal}
      {allocateStock.modal}
      {orderPartsWizard.wizard}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.sales_order_line_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableSelection: true,
          enableDownload: true,
          params: {
            order: orderId,
            part_detail: true
          },
          rowActions: rowActions,
          tableActions: tableActions,
          tableFilters: tableFilters,
          rowExpansion: rowExpansion
        }}
      />
    </>
  );
}
