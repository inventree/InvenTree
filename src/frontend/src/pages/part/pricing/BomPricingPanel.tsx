import { t } from '@lingui/macro';
import {
  Group,
  SegmentedControl,
  SimpleGrid,
  Stack,
  Text
} from '@mantine/core';
import { ReactNode, useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

import { CHART_COLORS } from '../../../components/charts/colors';
import { tooltipFormatter } from '../../../components/charts/tooltipFormatter';
import {
  formatCurrency,
  formatDecimal,
  formatPriceRange
} from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { ModelType } from '../../../enums/ModelType';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../../../tables/Column';
import { DateColumn, PartColumn } from '../../../tables/ColumnRenderers';
import { InvenTreeTable } from '../../../tables/InvenTreeTable';
import { LoadingPricingData, NoPricingData } from './PricingPanel';

// Display BOM data as a pie chart
function BomPieChart({
  data,
  currency
}: {
  readonly data: any[];
  readonly currency: string;
}) {
  return (
    <ResponsiveContainer width="100%" height={500}>
      <PieChart>
        <Pie
          data={data}
          dataKey="total_price_min"
          nameKey="name"
          innerRadius={20}
          outerRadius={100}
        >
          {data.map((_entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={CHART_COLORS[index % CHART_COLORS.length]}
            />
          ))}
        </Pie>
        <Pie
          data={data}
          dataKey="total_price_max"
          nameKey="name"
          innerRadius={120}
          outerRadius={240}
        >
          {data.map((_entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={CHART_COLORS[index % CHART_COLORS.length]}
            />
          ))}
        </Pie>
        <Tooltip
          formatter={(label, payload) => tooltipFormatter(label, currency)}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

// Display BOM data as a bar chart
function BomBarChart({
  data,
  currency
}: {
  readonly data: any[];
  readonly currency: string;
}) {
  return (
    <ResponsiveContainer width="100%" height={500}>
      <BarChart data={data}>
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
        <Legend />
        <Bar
          dataKey="total_price_min"
          fill={CHART_COLORS[0]}
          label={t`Minimum Total Price`}
        />
        <Bar
          dataKey="total_price_max"
          fill={CHART_COLORS[1]}
          label={t`Maximum Total Price`}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}

export default function BomPricingPanel({
  part,
  pricing
}: {
  readonly part: any;
  readonly pricing: any;
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
        render: (record: any) => {
          let quantity = formatDecimal(record.quantity);
          let units = record.sub_part_detail?.units;

          return (
            <Group justify="space-between" grow>
              <Text>{quantity}</Text>
              {units && <Text size="xs">[{units}]</Text>}
            </Group>
          );
        }
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

  const [chartType, setChartType] = useState<string>('pie');

  const hasData: boolean = useMemo(() => {
    return !table.isLoading && bomPricingData.length > 0;
  }, [table.isLoading, bomPricingData.length]);

  return (
    <Stack gap="xs">
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
            enableSelection: false,
            modelType: ModelType.part,
            modelField: 'sub_part'
          }}
        />
        <Stack gap="xs">
          {table.isLoading && <LoadingPricingData />}
          {hasData && (
            <Stack gap="xs">
              {chartType == 'bar' && (
                <BomBarChart
                  data={bomPricingData}
                  currency={pricing?.currency}
                />
              )}
              {chartType == 'pie' && (
                <BomPieChart
                  data={bomPricingData}
                  currency={pricing?.currency}
                />
              )}
              <SegmentedControl
                value={chartType}
                onChange={setChartType}
                data={[
                  { value: 'pie', label: t`Pie Chart` },
                  { value: 'bar', label: t`Bar Chart` }
                ]}
              />
            </Stack>
          )}
          {!hasData && !table.isLoading && <NoPricingData />}
        </Stack>
      </SimpleGrid>
    </Stack>
  );
}
