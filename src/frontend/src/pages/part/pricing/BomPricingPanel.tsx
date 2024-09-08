import { t } from '@lingui/macro';
import { BarChart, DonutChart } from '@mantine/charts';
import {
  Center,
  Group,
  SegmentedControl,
  SimpleGrid,
  Stack,
  Text
} from '@mantine/core';
import { ReactNode, useMemo, useState } from 'react';

import { CHART_COLORS } from '../../../components/charts/colors';
import { tooltipFormatter } from '../../../components/charts/tooltipFormatter';
import { formatDecimal, formatPriceRange } from '../../../defaults/formatters';
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
  // Construct donut data
  const maxPricing = useMemo(() => {
    return (
      data
        ?.filter((el: any) => !!el.total_price_max)
        .map((entry, index) => {
          return {
            // Note: Replace '.' in name to avoid issues with tooltip
            name: entry?.name?.replace('.', '') ?? '',
            value: entry?.total_price_max,
            color: CHART_COLORS[index % CHART_COLORS.length] + '.5'
          };
        }) ?? []
    );
  }, [data]);

  return (
    <Center>
      <DonutChart
        data={maxPricing}
        size={500}
        thickness={80}
        withLabels={false}
        withLabelsLine={false}
        tooltipDataSource="segment"
        chartLabel={t`Total Price`}
        valueFormatter={(value) => tooltipFormatter(value, currency)}
      />
    </Center>
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
    <BarChart
      h={500}
      dataKey="name"
      data={data}
      xAxisLabel={t`Component`}
      yAxisLabel={t`Price Range`}
      series={[
        { name: 'total_price_min', label: t`Minimum Price`, color: 'blue.6' },
        { name: 'total_price_max', label: t`Maximum Price`, color: 'teal.6' }
      ]}
      valueFormatter={(value) => tooltipFormatter(value, currency)}
    />
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
    return !table.isLoading && bomPricingData && bomPricingData.length > 0;
  }, [table.isLoading, bomPricingData]);

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
