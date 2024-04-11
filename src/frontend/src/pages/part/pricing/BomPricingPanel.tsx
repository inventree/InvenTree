import { t } from '@lingui/macro';
import { SimpleGrid, Stack } from '@mantine/core';
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
import { formatDecimal, formatPriceRange } from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../../../tables/Column';
import { DateColumn, PartColumn } from '../../../tables/ColumnRenderers';
import { InvenTreeTable } from '../../../tables/InvenTreeTable';
import { NoPricingData } from './PricingPanel';

export default function BomPricingPanel({
  part,
  pricing
}: {
  part: any;
  pricing: any;
}): ReactNode {
  const table = useTable('pricing-bom');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Component`,
        sortable: true,
        switchable: false,
        render: (record: any) => PartColumn(record.sub_part_detail)
      },
      {
        accessor: 'quantity',
        title: t`Quantity`,
        sortable: true,
        switchable: false,
        render: (record: any) => formatDecimal(record.quantity)
      },
      {
        accessor: 'unit_price',
        ordering: 'pricing_max',
        sortable: true,
        switchable: true,
        title: t`Unit Price`,
        render: (record: any) => {
          return formatPriceRange(record.pricing_min, record.pricing_max, {
            currency: pricing?.currency
          });
        }
      },
      {
        accessor: 'total_price',
        title: t`Total Price`,
        ordering: 'pricing_max_total',
        sortable: true,
        switchable: false,
        render: (record: any) => {
          return formatPriceRange(
            record.pricing_min_total,
            record.pricing_max_total,
            {
              currency: pricing?.currency
            }
          );
        }
      },
      DateColumn({
        accessor: 'pricing_updated',
        title: t`Updated`,
        sortable: true,
        switchable: true
      })
    ];
  }, [part, pricing]);

  const bomPricingData: any[] = useMemo(() => {
    const pricing = table.records.map((entry: any) => {
      return {
        name: entry.sub_part_detail?.name,
        unit_price_min: parseFloat(entry.pricing_min ?? 0),
        unit_price_max: parseFloat(entry.pricing_max ?? 0),
        total_price_min: parseFloat(entry.pricing_min_total ?? 0),
        total_price_max: parseFloat(entry.pricing_max_total ?? 0)
      };
    });

    return pricing;
  }, [table.records]);

  return (
    <Stack spacing="xs">
      <SimpleGrid cols={2}>
        <InvenTreeTable
          tableState={table}
          url={apiUrl(ApiEndpoints.bom_list)}
          columns={columns}
          props={{
            params: {
              part: part?.pk,
              sub_part_detail: true,
              has_pricing: true
            },
            enableSelection: false
          }}
        />
        {bomPricingData.length > 0 ? (
          <ResponsiveContainer width="100%" height={500}>
            <BarChart data={bomPricingData}>
              <XAxis dataKey="name" />
              <YAxis
                yAxisId="left"
                orientation="left"
                stroke={CHART_COLORS[1]}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke={CHART_COLORS[3]}
              />
              <Tooltip />
              <Legend />
              <Bar
                dataKey="unit_price_min"
                yAxisId="left"
                fill={CHART_COLORS[0]}
                label={t`Minimum Unit Price`}
              />
              <Bar
                dataKey="unit_price_max"
                yAxisId="left"
                fill={CHART_COLORS[1]}
                label={t`Maximum Unit Price`}
              />
              <Bar
                dataKey="total_price_min"
                yAxisId="right"
                fill={CHART_COLORS[2]}
                label={t`Minimum Total Price`}
              />
              <Bar
                dataKey="total_price_max"
                yAxisId="right"
                fill={CHART_COLORS[3]}
                label={t`Maximum Total Price`}
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <NoPricingData />
        )}
      </SimpleGrid>
    </Stack>
  );
}
