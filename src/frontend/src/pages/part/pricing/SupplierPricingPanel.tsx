import { t } from '@lingui/macro';
import { BarChart } from '@mantine/charts';
import { SimpleGrid } from '@mantine/core';
import { useMemo } from 'react';

import { tooltipFormatter } from '../../../components/charts/tooltipFormatter';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import type { TableColumn } from '../../../tables/Column';
import { InvenTreeTable } from '../../../tables/InvenTreeTable';
import {
  SupplierPriceBreakColumns,
  calculateSupplierPartUnitPrice
} from '../../../tables/purchasing/SupplierPriceBreakTable';
import { NoPricingData } from './PricingPanel';

export default function SupplierPricingPanel({
  part
}: Readonly<{ part: any }>) {
  const table = useTable('pricingsupplier');

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
    return (
      table.records?.map((record: any) => {
        return {
          quantity: record.quantity,
          supplier_price: Number.parseFloat(record.price),
          unit_price: calculateSupplierPartUnitPrice(record),
          name: record.part_detail?.SKU
        };
      }) ?? []
    );
  }, [table.records]);

  return (
    <SimpleGrid cols={{ base: 1, md: 2 }}>
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
        <BarChart
          data={supplierPricingData}
          dataKey='name'
          series={[
            { name: 'unit_price', label: t`Unit Price`, color: 'blue.6' },
            {
              name: 'supplier_price',
              label: t`Supplier Price`,
              color: 'teal.6'
            }
          ]}
          valueFormatter={(value) => tooltipFormatter(value, currency)}
        />
      ) : (
        <NoPricingData />
      )}
    </SimpleGrid>
  );
}
