import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import {
  IconShoppingCart,
  IconSquareArrowRight,
  IconTools
} from '@tabler/icons-react';
import { ReactNode, useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ProgressBar } from '../../components/items/ProgressBar';
import { formatCurrency } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useSalesOrderLineItemFields } from '../../forms/SalesOrderForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { DateColumn, LinkColumn, PartColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import {
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction
} from '../RowActions';
import { TableHoverCard } from '../TableHoverCard';

export default function SalesOrderLineItemTable({
  orderId,
  customerId
}: {
  orderId: number;
  customerId: number;
}) {
  const user = useUserState();
  const table = useTable('sales-order-line-item');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        sortable: true,
        switchable: false,
        render: (record: any) => PartColumn(record?.part_detail)
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
          let part_stock = record?.available_stock ?? 0;
          let variant_stock = record?.available_variant_stock ?? 0;
          let available = part_stock + variant_stock;

          let required = Math.max(
            record.quantity - record.allocated - record.shipped,
            0
          );

          let color: string | undefined = undefined;
          let text: string = `${available}`;

          let extra: ReactNode[] = [];

          if (available <= 0) {
            color = 'red';
            text = t`No stock available`;
          } else if (available < required) {
            color = 'orange';
          }

          if (variant_stock > 0) {
            extra.push(<Text size="sm">{t`Includes variant stock`}</Text>);
          }

          return (
            <TableHoverCard
              value={<Text color={color}>{text}</Text>}
              extra={extra}
              title={t`Stock Information`}
            />
          );
        }
      },
      {
        accessor: 'allocated',
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
  }, []);

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
    initialData: initialData,
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

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        tooltip={t`Add line item`}
        onClick={() => {
          setInitialData({
            order: orderId
          });
          newLine.open();
        }}
        hidden={!user.hasAddRole(UserRoles.sales_order)}
      />
    ];
  }, [user, orderId]);

  const rowActions = useCallback(
    (record: any) => {
      const allocated = (record?.allocated ?? 0) > (record?.quantity ?? 0);

      return [
        {
          hidden: allocated || !user.hasChangeRole(UserRoles.sales_order),
          title: t`Allocate stock`,
          icon: <IconSquareArrowRight />,
          color: 'green'
        },
        {
          hidden:
            allocated ||
            !user.hasAddRole(UserRoles.build) ||
            !record?.part_detail?.assembly,
          title: t`Build stock`,
          icon: <IconTools />,
          color: 'blue'
        },
        {
          hidden:
            allocated ||
            !user.hasAddRole(UserRoles.purchase_order) ||
            !record?.part_detail?.purchaseable,
          title: t`Order stock`,
          icon: <IconShoppingCart />,
          color: 'blue'
        },
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.sales_order),
          onClick: () => {
            setSelectedLine(record.pk);
            editLine.open();
          }
        }),
        RowDuplicateAction({
          hidden: !user.hasAddRole(UserRoles.sales_order),
          onClick: () => {
            setInitialData(record);
            newLine.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.sales_order),
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
      {editLine.modal}
      {deleteLine.modal}
      {newLine.modal}
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
          modelType: ModelType.part,
          modelField: 'part'
        }}
      />
    </>
  );
}
