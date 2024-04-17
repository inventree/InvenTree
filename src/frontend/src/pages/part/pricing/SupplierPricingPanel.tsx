import { t } from '@lingui/macro';
import { SimpleGrid } from '@mantine/core';
import { useMemo } from 'react';
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

import { CHART_COLORS } from '../../../components/charts/colors';
import { tooltipFormatter } from '../../../components/charts/tooltipFormatter';
import { formatCurrency } from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../../../tables/Column';
import { InvenTreeTable } from '../../../tables/InvenTreeTable';
import {
  SupplierPriceBreakColumns,
  calculateSupplierPartUnitPrice
} from '../../../tables/purchasing/SupplierPriceBreakTable';
import { NoPricingData } from './PricingPanel';

export default function SupplierPricingPanel({ part }: { part: any }) {
  const table = useTable('pricing-supplier');

  const columns: TableColumn[] = useMemo(() => {
    return SupplierPriceBreakColumns();
  }, []);

  const currency: string = useMemo(() => {
    if (table.records.length === 0) {
      return '';
    }
    return table.records[0].currency;
  }, [table.records]);

  const supplierPricingData = useMemo(() => {
    return table.records.map((record: any) => {
      return {
        quantity: record.quantity,
        supplier_price: record.price,
        unit_price: calculateSupplierPartUnitPrice(record),
        name: record.part_detail?.SKU
      };
    });
  }, [table.records]);

  return (
    <SimpleGrid cols={2}>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.supplier_part_pricing_list)}
        columns={columns}
        tableState={table}
        props={{
          params: {
            base_part: part.pk,
            supplier_detail: true,
            part_detail: true
          }
        }}
      />
      {supplierPricingData.length > 0 ? (
        <ResponsiveContainer width="100%" height={500}>
          <BarChart data={supplierPricingData}>
            <XAxis dataKey="name" />
            <YAxis
              tickFormatter={(value, index) =>
                formatCurrency(value, {
                  currency: currency
                })?.toString() ?? ''
              }
            />
            <Tooltip
              formatter={(label, payload) => tooltipFormatter(label, currency)}
            />
            <Bar
              dataKey="unit_price"
              fill={CHART_COLORS[0]}
              label={t`Unit Price`}
            />
            <Bar
              dataKey="supplier_price"
              fill="#82ca9d"
              label={t`Supplier Price`}
            />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <NoPricingData />
      )}
    </SimpleGrid>
  );
}
