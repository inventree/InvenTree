import { t } from '@lingui/core/macro';
import { Text } from '@mantine/core';
import { useMemo } from 'react';

import { ProgressBar } from '@lib/components/ProgressBar';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { formatCurrency, formatDecimal } from '../../defaults/formatters';
import { useTable } from '../../hooks/UseTable';
import { DateColumn, ReferenceColumn, StatusColumn } from '../ColumnRenderers';
import { IncludeVariantsFilter, StatusFilterOptions } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

export default function PartPurchaseOrdersTable({
  partId
}: Readonly<{
  partId: number;
}>) {
  const table = useTable('partpurchaseorders');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      ReferenceColumn({
        accessor: 'order_detail.reference',
        ordering: 'order',
        sortable: true,
        switchable: false,
        title: t`Purchase Order`
      }),
      StatusColumn({
        accessor: 'order_detail.status',
        sortable: true,
        ordering: 'status',
        title: t`Status`,
        model: ModelType.purchaseorder
      }),
      {
        accessor: 'order_detail.supplier_name',
        title: t`Supplier`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'supplier_part_detail.SKU',
        ordering: 'sku',
        title: t`Supplier Part`,
        sortable: true
      },
      {
        accessor: 'supplier_part_detail.manufacturer_part_detail.MPN',
        ordering: 'mpn',
        title: t`Manufacturer Part`,
        sortable: true
      },
      {
        accessor: 'quantity',
        sortable: true,
        switchable: false,
        render: (record: any) => {
          const supplier_part = record?.supplier_part_detail ?? {};
          const part = record?.part_detail ?? supplier_part?.part_detail ?? {};
          const extra = [];

          if (supplier_part.pack_quantity_native != 1) {
            const total = record.quantity * supplier_part.pack_quantity_native;

            extra.push(
              <Text key='pack-quantity' size='sm'>
                {t`Pack Quantity`}: {supplier_part.pack_quantity}
              </Text>
            );

            extra.push(
              <Text key='total-quantity' size='sm'>
                {t`Total Quantity`}: {formatDecimal(total)} {part?.units}
              </Text>
            );
          }

          return (
            <TableHoverCard
              value={
                <ProgressBar
                  value={record.received}
                  maximum={record.quantity}
                  progressLabel
                />
              }
              extra={extra}
              title={t`Quantity`}
            />
          );
        }
      },
      DateColumn({
        accessor: 'target_date',
        title: t`Target Date`
      }),
      DateColumn({
        accessor: 'order_detail.complete_date',
        ordering: 'complete_date',
        title: t`Completion Date`
      }),
      {
        accessor: 'purchase_price',
        render: (record: any) =>
          formatCurrency(record.purchase_price, {
            currency: record.purchase_price_currency
          })
      }
    ];
  }, []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'pending',
        label: t`Pending`,
        description: t`Show pending orders`
      },
      {
        name: 'received',
        label: t`Received`,
        description: t`Show received items`
      },
      {
        name: 'order_status',
        label: t`Order Status`,
        description: t`Filter by order status`,
        choiceFunction: StatusFilterOptions(ModelType.purchaseorder)
      },
      IncludeVariantsFilter()
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.purchase_order_line_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          base_part: partId,
          part_detail: true,
          order_detail: true,
          supplier_detail: true
        },
        modelField: 'order',
        modelType: ModelType.purchaseorder,
        tableFilters: tableFilters
      }}
    />
  );
}
