import { t } from '@lingui/macro';
import { SimpleGrid } from '@mantine/core';
import { ReactNode, useCallback, useMemo } from 'react';
import {
  Bar,
  BarChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

import { formatCurrency, renderDate } from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../../../tables/Column';
import { InvenTreeTable } from '../../../tables/InvenTreeTable';

export default function PurchacseHistoryPanel({
  part
}: {
  part: any;
}): ReactNode {
  const table = useTable('pricing-purchase-history');

  const calculateUnitPrice = useCallback((record: any) => {
    let pack_quantity = record?.supplier_part_detail?.pack_quantity_native ?? 1;
    let unit_price = record.purchase_price / pack_quantity;

    return unit_price;
  }, []);

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'order',
        title: t`Purchase Order`,
        render: (record: any) => record?.order_detail?.reference,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'order_detail.complete_date',
        title: t`Date`,
        sortable: false,
        switchable: true,
        render: (record: any) => renderDate(record.order_detail.complete_date)
      },
      {
        accessor: 'purchase_price',
        title: t`Purchase Price`,
        sortable: true,
        switchable: true,
        render: (record: any) =>
          formatCurrency(record.purchase_price, {
            currency: record.purchase_price_currency
          })
      },
      {
        accessor: 'unit_price',
        title: t`Unit Price`,
        ordering: 'purchase_price',
        sortable: true,
        switchable: false,
        render: (record: any) => {
          return formatCurrency(calculateUnitPrice(record), {
            currency: record.purchase_price_currency
          });
        }
      }
    ];
  }, []);

  const purchaseHistoryData = useMemo(() => {
    return table.records.map((record: any) => {
      return {
        quantity: record.quantity,
        purchase_price: calculateUnitPrice(record),
        name: record.order_detail.reference
      };
    });
  }, [table.records]);

  return (
    <SimpleGrid cols={2}>
      <InvenTreeTable
        tableState={table}
        url={apiUrl(ApiEndpoints.purchase_order_line_list)}
        columns={columns}
        props={{
          params: {
            base_part: part.pk,
            part_detail: true,
            order_detail: true,
            has_pricing: true,
            order_complete: true
          }
        }}
      />
      <ResponsiveContainer width="100%" height={500}>
        <BarChart data={table.records}>
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar
            dataKey="purchase_price"
            fill="#8884d8"
            label={t`Purchase Price`}
          />
        </BarChart>
      </ResponsiveContainer>
    </SimpleGrid>
  );
}
