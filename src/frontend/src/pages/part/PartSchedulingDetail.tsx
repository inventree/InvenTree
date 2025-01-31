import { t } from '@lingui/macro';
import { type ChartTooltipProps, LineChart } from '@mantine/charts';
import {
  Alert,
  Center,
  Divider,
  Loader,
  Paper,
  SimpleGrid,
  Text
} from '@mantine/core';
import { type ReactNode, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { formatDate } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { navigateToLink } from '../../functions/navigation';
import { getDetailUrl } from '../../functions/urls';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import type { TableColumn } from '../../tables/Column';
import { DateColumn, DescriptionColumn } from '../../tables/ColumnRenderers';
import { InvenTreeTable } from '../../tables/InvenTreeTable';
import { TableHoverCard } from '../../tables/TableHoverCard';

/*
 * Render a tooltip for the chart, with correct date information
 */
function ChartTooltip({ label, payload }: Readonly<ChartTooltipProps>) {
  if (!payload) {
    return null;
  }

  if (label && typeof label == 'number') {
    label = formatDate(new Date(label).toISOString());
  }

  const scheduled = payload.find((item) => item.name == 'scheduled');
  const minimum = payload.find((item) => item.name == 'minimum');
  const maximum = payload.find((item) => item.name == 'maximum');

  return (
    <Paper px='md' py='sm' withBorder shadow='md' radius='md'>
      <Text key='title'>{label}</Text>
      <Divider />
      <Text key='maximum' c={maximum?.color} fz='sm'>
        {t`Maximum`} : {maximum?.value}
      </Text>
      <Text key='scheduled' c={scheduled?.color} fz='sm'>
        {t`Scheduled`} : {scheduled?.value}
      </Text>
      <Text key='minimum' c={minimum?.color} fz='sm'>
        {t`Minimum`} : {minimum?.value}
      </Text>
    </Paper>
  );
}

export default function PartSchedulingDetail({
  part
}: Readonly<{ part: any }>) {
  const table = useTable('part-scheduling');
  const navigate = useNavigate();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'label',
        switchable: false,
        title: t`Order`
      },
      DescriptionColumn({
        accessor: 'title',
        switchable: false
      }),
      DateColumn({
        sortable: false,
        switchable: false
      }),
      {
        accessor: 'quantity',
        title: t`Quantity`,
        switchable: false,
        render: (record: any) => {
          let q = record.quantity;
          const extra: ReactNode[] = [];

          if (record.speculative_quantity != 0) {
            q = record.speculative_quantity;
            extra.push(
              <Text
                size='sm'
                key={'speculative'}
              >{t`Quantity is speculative`}</Text>
            );
          }

          if (!record.date) {
            extra.push(
              <Text
                key={'null-date'}
                size='sm'
              >{t`No date available for provided quantity`}</Text>
            );
          } else if (new Date(record.date) < new Date()) {
            extra.push(
              <Text size='sm' key={'past-date'}>{t`Date is in the past`}</Text>
            );
          }

          return (
            <TableHoverCard
              value={<Text key='quantity'>{q}</Text>}
              title={t`Scheduled Quantity`}
              extra={extra}
            />
          );
        }
      }
    ];
  }, []);

  const chartData = useMemo(() => {
    /* Rebuild chart data whenever the table data changes.
     * Note: We assume that the data is provided in increasing date order,
     *       with "null" date entries placed first.
     */

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Date bounds
    let min_date: Date = new Date();
    let max_date: Date = new Date();

    // Track stock scheduling throughout time
    let stock = part.in_stock ?? 0;
    let stock_min = stock;
    let stock_max = stock;

    // First, iterate through each entry and find any entries without an associated date, or in the past
    table.records.forEach((record) => {
      const q = record.quantity + record.speculative_quantity;

      if (record.date == null || new Date(record.date) < today) {
        if (q < 0) {
          stock_min += q;
        } else {
          stock_max += q;
        }
      }
    });

    // Construct initial chart entry (for today)
    const entries: any[] = [
      {
        // date: formatDate(today.toISOString()),
        date: today.valueOf(),
        delta: 0,
        scheduled: stock,
        minimum: stock_min,
        maximum: stock_max,
        low_stock: part.minimum_stock
      }
    ];

    table.records.forEach((record) => {
      const q = record.quantity + record.speculative_quantity;

      if (!record.date) {
        return;
      }

      const date = new Date(record.date);

      // In the past? Ignore this entry
      if (date < today) {
        return;
      }

      // Update date limits

      if (date < min_date) {
        min_date = date;
      }

      if (date > max_date) {
        max_date = date;
      }

      // Update stock levels
      stock += record.quantity;

      stock_min += record.quantity;
      stock_max += record.quantity;

      // Speculative quantities expand the expected stock range
      if (record.speculative_quantity < 0) {
        stock_min += record.speculative_quantity;
      } else if (record.speculative_quantity > 0) {
        stock_max += record.speculative_quantity;
      }

      entries.push({
        ...record,
        date: new Date(record.date).valueOf(),
        scheduled: stock,
        minimum: stock_min,
        maximum: stock_max,
        low_stock: part.minimum_stock
      });
    });

    return entries;
  }, [part, table.records]);

  // Calculate the date limits of the chart
  const chartLimits: number[] = useMemo(() => {
    let min_date = new Date();
    let max_date = new Date();

    if (chartData.length > 0) {
      min_date = new Date(chartData[0].date);
      max_date = new Date(chartData[chartData.length - 1].date);
    }

    // Expand limits by one day on either side
    min_date.setDate(min_date.getDate() - 1);
    max_date.setDate(max_date.getDate() + 1);

    return [min_date.valueOf(), max_date.valueOf()];
  }, [chartData]);

  const hasSchedulingInfo: boolean = useMemo(
    () => table.recordCount > 0,
    [table.recordCount]
  );

  return (
    <>
      {!table.isLoading && !hasSchedulingInfo && (
        <Alert color='blue' title={t`No information available`}>
          <Text>{t`There is no scheduling information available for the selected part`}</Text>
        </Alert>
      )}
      <SimpleGrid cols={{ base: 1, md: 2 }}>
        <InvenTreeTable
          url={apiUrl(ApiEndpoints.part_scheduling, part.pk)}
          tableState={table}
          columns={tableColumns}
          props={{
            enableSearch: false,
            onRowClick: (record: any, index: number, event: any) => {
              const url = getDetailUrl(record.model, record.model_id);

              if (url) {
                navigateToLink(url, navigate, event);
              }
            }
          }}
        />
        {table.isLoading ? (
          <Center>
            <Loader />
          </Center>
        ) : (
          <LineChart
            data={chartData}
            mah={'500px'}
            dataKey='date'
            withLegend
            withYAxis
            tooltipProps={{
              content: ({ label, payload }) => (
                <ChartTooltip label={label} payload={payload} />
              )
            }}
            yAxisLabel={t`Expected Quantity`}
            xAxisLabel={t`Date`}
            xAxisProps={{
              domain: chartLimits,
              scale: 'time',
              type: 'number',
              tickFormatter: (value: number) => {
                return formatDate(new Date(value).toISOString());
              }
            }}
            series={[
              {
                name: 'scheduled',
                label: t`Scheduled`,
                color: 'blue.6'
              },
              {
                name: 'minimum',
                label: t`Minimum`,
                color: 'yellow.6'
              },
              {
                name: 'maximum',
                label: t`Maximum`,
                color: 'teal.6'
              },
              {
                name: 'low_stock',
                label: t`Low Stock`,
                color: 'red.6'
              }
            ]}
          />
        )}
      </SimpleGrid>
    </>
  );
}
