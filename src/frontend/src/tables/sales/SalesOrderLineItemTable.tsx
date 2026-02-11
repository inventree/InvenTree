import { t } from '@lingui/core/macro';
import { Group, Paper, Text } from '@mantine/core';
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

import { ActionButton } from '@lib/components/ActionButton';
import { AddItemButton } from '@lib/components/AddItemButton';
import { ProgressBar } from '@lib/components/ProgressBar';
import {
  type RowAction,
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction,
  RowViewAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { RenderPart } from '../../components/render/Part';
import OrderPartsWizard from '../../components/wizards/OrderPartsWizard';
import { formatCurrency, formatDecimal } from '../../defaults/formatters';
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
import { useUserState } from '../../states/UserState';
import {
  DateColumn,
  DecimalColumn,
  DescriptionColumn,
  LinkColumn,
  ProjectCodeColumn,
  RenderPartColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import RowExpansionIcon from '../RowExpansionIcon';
import { TableHoverCard } from '../TableHoverCard';
import SalesOrderAllocationTable from './SalesOrderAllocationTable';

export default function SalesOrderLineItemTable({
  orderId,
  orderDetailRefresh,
  currency,
  customerId,
  editable
}: Readonly<{
  orderId: number;
  orderDetailRefresh: () => void;
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
        minWidth: 175,
        render: (record: any) => {
          return (
            <Group wrap='nowrap'>
              {record.part_detail?.virtual || (
                <RowExpansionIcon
                  enabled={record.allocated}
                  expanded={table.isRowExpanded(record.pk)}
                />
              )}
              <RenderPartColumn part={record.part_detail} />
            </Group>
          );
        }
      },
      {
        accessor: 'part_detail.IPN',
        title: t`IPN`,
        sortable: true,
        ordering: 'IPN',
        switchable: true
      },
      DescriptionColumn({
        accessor: 'part_detail.description'
      }),
      {
        accessor: 'reference',
        sortable: false,
        switchable: true
      },
      ProjectCodeColumn({}),
      DecimalColumn({
        accessor: 'quantity',
        sortable: true
      }),
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
          if (record.part_detail?.virtual) {
            return <Text size='sm' fs='italic'>{t`Virtual part`}</Text>;
          }

          const part_stock = record?.available_stock ?? 0;
          const variant_stock = record?.available_variant_stock ?? 0;
          const available = part_stock + variant_stock;

          const required = Math.max(
            record.quantity - record.allocated - record.shipped,
            0
          );

          let color: string | undefined;
          let text = `${formatDecimal(available)}`;

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
                {t`In production`}: {formatDecimal(record.building)}
              </Text>
            );
          }

          if (record.on_order > 0) {
            extra.push(
              <Text size='sm'>
                {t`On order`}: {formatDecimal(record.on_order)}
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
        render: (record: any) => {
          if (record.part_detail?.virtual) {
            return <Text size='sm' fs='italic'>{t`Virtual part`}</Text>;
          }

          return (
            <ProgressBar
              progressLabel={true}
              value={record.allocated}
              maximum={record.quantity}
            />
          );
        }
      },
      {
        accessor: 'shipped',
        sortable: true,
        render: (record: any) => {
          if (record.part_detail?.virtual) {
            return <Text size='sm' fs='italic'>{t`Virtual part`}</Text>;
          }

          return (
            <ProgressBar
              progressLabel={true}
              value={record.shipped}
              maximum={record.quantity}
            />
          );
        }
      },
      {
        accessor: 'notes'
      },
      LinkColumn({
        accessor: 'link'
      })
    ];
  }, [table.isRowExpanded]);

  const [selectedLineId, setSelectedLineId] = useState<number>(0);

  const [selectedSupplierPart, setSelectedSupplierPart] = useState<any>(null);

  const [initialData, setInitialData] = useState({});

  const createLineFields = useSalesOrderLineItemFields({
    orderId: orderId,
    customerId: customerId,
    create: true,
    currency: currency
  });

  const newLine = useCreateApiFormModal({
    url: ApiEndpoints.sales_order_line_list,
    title: t`Add Line Item`,
    fields: createLineFields,
    initialData: {
      ...initialData,
      sale_price_currency: currency
    },
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const editLineFields = useSalesOrderLineItemFields({
    orderId: orderId,
    customerId: customerId,
    create: false
  });

  const editLine = useEditApiFormModal({
    url: ApiEndpoints.sales_order_line_list,
    pk: selectedLineId,
    title: t`Edit Line Item`,
    fields: editLineFields,
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const deleteLine = useDeleteApiFormModal({
    url: ApiEndpoints.sales_order_line_list,
    pk: selectedLineId,
    title: t`Delete Line Item`,
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const allocateSerialFields = useSalesOrderAllocateSerialsFields({
    itemId: selectedLineId,
    orderId: orderId
  });

  const allocateBySerials = useCreateApiFormModal({
    url: ApiEndpoints.sales_order_allocate_serials,
    pk: orderId,
    title: t`Allocate Serial Numbers`,
    preFormContent: selectedSupplierPart ? (
      <Paper withBorder p='sm'>
        <RenderPart instance={selectedSupplierPart} />
      </Paper>
    ) : undefined,
    initialData: initialData,
    fields: allocateSerialFields,
    table: table
  });

  const buildOrderFields = useBuildOrderFields({
    create: true,
    modalId: 'build-order-create-from-sales-order'
  });

  const newBuildOrder = useCreateApiFormModal({
    url: ApiEndpoints.build_order_list,
    title: t`Create Build Order`,
    modalId: 'build-order-create-from-sales-order',
    fields: buildOrderFields,
    initialData: initialData,
    follow: true,
    modelType: ModelType.build
  });

  const [selectedItems, setSelectedItems] = useState<any[]>([]);

  const allocateStock = useAllocateToSalesOrderForm({
    orderId: orderId,
    lineItems: selectedItems.filter(
      (item) => item.part_detail?.virtual !== true
    ),
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
      const virtual = record?.part_detail?.virtual ?? false;

      return [
        {
          hidden:
            allocated ||
            virtual ||
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
            virtual ||
            !editable ||
            !user.hasChangeRole(UserRoles.sales_order),
          title: t`Allocate serials`,
          icon: <IconHash />,
          color: 'green',
          onClick: () => {
            setSelectedLineId(record.pk);
            setSelectedSupplierPart(record?.part_detail ?? null);
            setInitialData({
              quantity: record.quantity - record.allocated
            });
            allocateBySerials.open();
          }
        },
        {
          hidden:
            allocated ||
            virtual ||
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
            virtual ||
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
            setSelectedLineId(record.pk);
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
            setSelectedLineId(record.pk);
            deleteLine.open();
          }
        }),
        RowViewAction({
          title: t`View Part`,
          modelType: ModelType.part,
          modelId: record.part,
          navigate: navigate,
          hidden: !user.hasViewRole(UserRoles.part)
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
        if (record?.part_detail?.virtual) {
          return false;
        }
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
            allowEdit={true}
            modelTarget={ModelType.stockitem}
            modelField={'item'}
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
