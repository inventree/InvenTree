import { t } from '@lingui/macro';
import { BarChart } from '@mantine/charts';
import { SimpleGrid, Stack } from '@mantine/core';
import { type ReactNode, useMemo } from 'react';

import { tooltipFormatter } from '../../../components/charts/tooltipFormatter';
import { formatCurrency } from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { ModelType } from '../../../enums/ModelType';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import type { TableColumn } from '../../../tables/Column';
import { DateColumn, PartColumn } from '../../../tables/ColumnRenderers';
import { InvenTreeTable } from '../../../tables/InvenTreeTable';
import { NoPricingData } from './PricingPanel';

export default function VariantPricingPanel({
  part,
  pricing
}: Readonly<{
  part: any;
  pricing: any;
}>): ReactNode {
  const table = useTable('pricingvariants');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Variant Part`,
        sortable: true,
        switchable: false,
        render: (record: any) => PartColumn({ part: record, full_name: true })
      },
      {
        accessor: 'pricing_min',
        title: t`Minimum Price`,
        sortable: true,
        switchable: false,
        render: (record: any) =>
          formatCurrency(record.pricing_min, { currency: pricing?.currency })
      },
      {
        accessor: 'pricing_max',
        title: t`Maximum Price`,
        sortable: true,
        switchable: false,
        render: (record: any) =>
          formatCurrency(record.pricing_max, { currency: pricing?.currency })
      },
      DateColumn({
        accessor: 'pricing_updated',
        title: t`Updated`,
        sortable: true,
        switchable: true
      })
    ];
  }, []);

  // Calculate pricing data for the part variants
  const variantPricingData: any[] = useMemo(() => {
    const pricing = table.records.map((variant: any) => {
      return {
        part: variant,
        name: variant.full_name,
        pmin: variant.pricing_min ?? variant.pricing_max ?? 0,
        pmax: variant.pricing_max ?? variant.pricing_min ?? 0
      };
    });

    return pricing;
  }, [table.records]);

  return (
    <Stack gap='xs'>
      <SimpleGrid cols={{ base: 1, md: 2 }}>
        <InvenTreeTable
          tableState={table}
          url={apiUrl(ApiEndpoints.part_list)}
          columns={columns}
          props={{
            params: {
              ancestor: part?.pk,
              has_pricing: true
            },
            enablePagination: true,
            modelType: ModelType.part
          }}
        />
        {variantPricingData.length > 0 ? (
          <BarChart
            dataKey='name'
            data={variantPricingData}
            xAxisLabel={t`Variant Part`}
            yAxisLabel={t`Price Range`}
            series={[
              { name: 'pmin', label: t`Minimum Price`, color: 'blue.6' },
              { name: 'pmax', label: t`Maximum Price`, color: 'teal.6' }
            ]}
            valueFormatter={(value) =>
              tooltipFormatter(value, pricing?.currency)
            }
          />
        ) : (
          <NoPricingData />
        )}
      </SimpleGrid>
    </Stack>
  );
}
