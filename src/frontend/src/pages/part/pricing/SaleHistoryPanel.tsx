import { t } from '@lingui/macro';
import { BarChart } from '@mantine/charts';
import { SimpleGrid } from '@mantine/core';
import { type ReactNode, useMemo } from 'react';

import { formatCurrency } from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import type { TableColumn } from '../../../tables/Column';
import { DateColumn } from '../../../tables/ColumnRenderers';
import { InvenTreeTable } from '../../../tables/InvenTreeTable';
import { NoPricingData } from './PricingPanel';

export default function SaleHistoryPanel({
  part
}: Readonly<{ part: any }>): ReactNode {
  const table = useTable('pricingsalehistory');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'order',
        title: t`Sales Order`,
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
      DateColumn({
        accessor: 'order_detail.shipment_date',
        title: t`Date`,
        sortable: false,
        switchable: true
      }),
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

  const saleHistoryData = useMemo(() => {
    return table.records.map((record: any) => {
      return {
        name: record.order_detail.reference,
        sale_price: Number.parseFloat(record.sale_price)
      };
    });
  }, [table.records]);

  return (
    <SimpleGrid cols={{ base: 1, md: 2 }}>
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
        <BarChart
          data={saleHistoryData}
          dataKey='name'
          series={[
            { name: 'sale_price', label: t`Sale Price`, color: 'blue.6' }
          ]}
        />
      ) : (
        <NoPricingData />
      )}
    </SimpleGrid>
  );
}
