import { t } from '@lingui/macro';
import { SimpleGrid } from '@mantine/core';
import { ReactNode, useMemo } from 'react';
import {
  Bar,
  BarChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

import { CHART_COLORS } from '../../../components/charts/colors';
import { formatCurrency, renderDate } from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../../../tables/Column';
import { InvenTreeTable } from '../../../tables/InvenTreeTable';
import { NoPricingData } from './PricingPanel';

export default function SaleHistoryPanel({ part }: { part: any }): ReactNode {
  const table = useTable('pricing-sale-history');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'order',
        title: t`Sale Order`,
        render: (record: any) => record?.order_detail?.reference,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'customer',
        title: t`Customer`,
        sortable: true,
        switchable: true,
        render: (record: any) => record?.customer_detail?.name
      },
      {
        accessor: 'shipment_date',
        title: t`Date`,
        sortable: false,
        switchable: true,
        render: (record: any) => renderDate(record.order_detail.shipment_date)
      },
      {
        accessor: 'sale_price',
        title: t`Sale Price`,
        sortable: true,
        switchable: false,
        render: (record: any) => {
          return formatCurrency(record.sale_price, {
            currency: record.sale_price_currency
          });
        }
      }
    ];
  }, []);

  const currency: string = useMemo(() => {
    if (table.records.length === 0) {
      return '';
    }
    return table.records[0].sale_price_currency;
  }, [table.records]);

  const saleHistoryData = useMemo(() => {
    return table.records.map((record: any) => {
      return {
        name: record.order_detail.reference,
        sale_price: record.sale_price
      };
    });
  }, [table.records]);

  return (
    <SimpleGrid cols={2}>
      <InvenTreeTable
        tableState={table}
        url={apiUrl(ApiEndpoints.sales_order_line_list)}
        columns={columns}
        props={{
          params: {
            part: part.pk,
            part_detail: true,
            order_detail: true,
            customer_detail: true,
            has_pricing: true,
            order_complete: true
          }
        }}
      />
      {saleHistoryData.length > 0 ? (
        <ResponsiveContainer width="100%" height={500}>
          <BarChart data={saleHistoryData}>
            <XAxis dataKey="name" />
            <YAxis
              tickFormatter={(value, index) =>
                formatCurrency(value, {
                  currency: currency
                })?.toString() ?? ''
              }
            />
            <Tooltip />
            <Legend />
            <Bar
              dataKey="sale_price"
              fill={CHART_COLORS[0]}
              label={t`Sale Price`}
            />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <NoPricingData />
      )}
    </SimpleGrid>
  );
}
