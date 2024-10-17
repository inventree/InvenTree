import { t } from '@lingui/macro';
import { BarChart, BarChartSeries } from '@mantine/charts';
import { Card, Group, SegmentedControl, Stack, Text } from '@mantine/core';
import { DateValue, MonthPickerInput } from '@mantine/dates';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { useCallback, useMemo, useState } from 'react';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';
import { CHART_COLORS } from './colors';

type OrderHistoryPeriod = 'M' | 'Q' | 'Y';

/**
 * Display an "order history" graph based on the provided parameters
 */
export function OrderHistoryChart({
  endpoint,
  params
}: {
  endpoint: ApiEndpoints;
  params: Record<string, any>;
}) {
  const [startDate, setStartDate] = useState<Date>(
    dayjs().subtract(1, 'year').toDate()
  );

  const [endDate, setEndDate] = useState<Date>(dayjs().toDate());

  const [period, setPeriod] = useState<OrderHistoryPeriod>('M');

  const historyQuery = useQuery({
    queryKey: [
      'order-history',
      endpoint,
      startDate.toString(),
      endDate.toString(),
      period,
      JSON.stringify(params)
    ],
    queryFn: async () => {
      return api
        .get(apiUrl(endpoint), {
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
            <Stack gap={0}>
              <Text size="sm">{t`Select Grouping Period`}</Text>
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
            </Stack>
          </Group>
        </Card>
        <Card>
          <BarChart
            h={400}
            data={historyData}
            dataKey="date"
            type="stacked"
            series={parts}
          />
        </Card>
      </Stack>
    </>
  );
}
