import { t } from '@lingui/macro';
import { BarChart, BarChartSeries } from '@mantine/charts';
import {
  Accordion,
  Card,
  Group,
  SegmentedControl,
  Skeleton,
  Stack
} from '@mantine/core';
import { DateValue, MonthPickerInput } from '@mantine/dates';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { useCallback, useMemo, useState } from 'react';

import { api } from '../../App';
import { CHART_COLORS } from '../../components/charts/colors';
import { StylishText } from '../../components/items/StylishText';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';
import { SalesOrderTable } from '../../tables/sales/SalesOrderTable';

export type OrderHistoryPeriod = 'M' | 'Q' | 'Y';

/**
 * Display an "order history" graph based on the provided parameters
 */
function OrderHistoryGraph({ params }: { params: Record<string, any> }) {
  const [startDate, setStartDate] = useState<Date>(
    dayjs().subtract(1, 'year').toDate()
  );
  const [endDate, setEndDate] = useState<Date>(dayjs().toDate());

  const [period, setPeriod] = useState<OrderHistoryPeriod>('M');

  const historyQuery = useQuery({
    queryKey: [
      'order-history',
      startDate.toString(),
      endDate.toString(),
      period,
      JSON.stringify(params)
    ],
    queryFn: async () => {
      return api
        .get(apiUrl(ApiEndpoints.sales_order_history), {
          params: {
            ...params,
            period: period,
            start_date: dayjs(startDate).format('YYYY-MM-DD'),
            end_date: dayjs(endDate).format('YYYY-MM-DD')
          }
        })
        .then((res) => res.data)
        .catch(() => []);
    }
  });

  // Construct individual chart series for each returned part
  const parts: BarChartSeries[] = useMemo(() => {
    return (
      historyQuery.data?.map((item: any, index: number) => {
        let part = item?.part ?? -1;
        let part_detail = item?.part_detail ?? {};

        return {
          name: part.toString(),
          label: part_detail?.full_name ?? part_detail?.name ?? part,
          color: CHART_COLORS[index % CHART_COLORS.length]
        };
      }) ?? []
    );
  }, [historyQuery.data]);

  // Reconstruct the data to match the required BarChart format
  const historyData = useMemo(() => {
    let data: any = {};

    historyQuery.data?.forEach((item: any) => {
      let part: number = item?.part ?? -1;
      let partKey = part.toString();
      let entries: any[] = item?.sales_history ?? [];

      entries.forEach((entry: any) => {
        // Find a matching date entry in the data
        let dateEntry = data[entry.date] || {};
        dateEntry[partKey] = entry.quantity;
        data[entry.date] = dateEntry;
      });
    });

    // Sort the data by date
    let sortedData = Object.keys(data).sort();

    return sortedData.map((date) => {
      let dateData = data[date];

      return {
        date: date,
        ...dateData
      };
    });
  }, [historyQuery.data]);

  const onSetStartDate = useCallback(
    (value: DateValue) => {
      if (value && value < endDate) {
        setStartDate(value);
      }
    },
    [endDate]
  );

  const onSetEndDate = useCallback(
    (value: DateValue) => {
      if (value && value > startDate) {
        setEndDate(value);
      }
    },
    [startDate]
  );

  return (
    <>
      <Stack gap="xs">
        <Card style={{ width: '100%' }}>
          <Group gap="xs" justify="space-apart" flex={'flex'}>
            <Group gap="xs">
              <MonthPickerInput
                value={startDate}
                label={t`Start Date`}
                onChange={onSetStartDate}
              />
              <MonthPickerInput
                value={endDate}
                label={t`End Date`}
                onChange={onSetEndDate}
              />
            </Group>

            <SegmentedControl
              value={period}
              onChange={(value: string) =>
                setPeriod((value as OrderHistoryPeriod) ?? 'M')
              }
              data={[
                { value: 'M', label: t`Monthly` },
                { value: 'Q', label: t`Quarterly` },
                { value: 'Y', label: t`Yearly` }
              ]}
            />
          </Group>
        </Card>
        <BarChart
          h={400}
          data={historyData}
          dataKey="date"
          type="stacked"
          series={parts}
        />
      </Stack>
    </>
  );
}

/**
 * Construct a panel displaying sales order information for a given part.
 */
export default function PartSalesPanel({ part }: { part: any }) {
  return (
    <Accordion multiple defaultValue={['sales-history']}>
      <Accordion.Item value="sales-orders">
        <Accordion.Control>
          <StylishText size="lg">{t`Sales Orders`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          {part.pk ? <SalesOrderTable partId={part.pk} /> : <Skeleton />}
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value="sales-history">
        <Accordion.Control>
          <StylishText size="lg">{t`Sales History`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          {part.pk ? (
            <OrderHistoryGraph
              params={{
                part: part.pk,
                include_variants: true
              }}
            />
          ) : (
            <Skeleton />
          )}
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
