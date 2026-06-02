import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { StylishText } from '@lib/index';
import { t } from '@lingui/core/macro';
import { BarChart } from '@mantine/charts';
import { Box, LoadingOverlay, Stack } from '@mantine/core';
import { useDocumentVisibility } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { useMemo } from 'react';
import { useApi } from '../../../contexts/ApiContext';
import { useUserState } from '../../../states/UserState';
import type { DashboardWidgetProps } from '../DashboardWidget';

function OrderHistoryComponent({
  modelType,
  title
}: {
  modelType: ModelType;
  title: string;
}) {
  const modelInfo = useMemo(() => {
    return ModelInformationDict[modelType];
  }, [modelType]);

  const url = useMemo(() => {
    return apiUrl(modelInfo.api_endpoint);
  }, [modelInfo]);

  const api = useApi();
  const visibility = useDocumentVisibility();

  const endDate = dayjs().add(1, 'day').format('YYYY-MM-DD');
  const startDate = dayjs()
    .subtract(12, 'month')
    .subtract(1, 'day')
    .format('YYYY-MM-DD');

  const params = {
    completed_after: startDate,
    completed_before: endDate
  };

  const query = useQuery({
    queryKey: ['dashboard-order-summary', modelType, params, visibility],
    enabled: visibility === 'visible',
    refetchOnWindowFocus: true,
    refetchOnMount: true,
    refetchInterval: 10 * 60 * 1000, // 10 minute refetch interval
    staleTime: 5 * 60 * 1000, // 5 minute stale time
    queryFn: () => {
      if (visibility !== 'visible') {
        return [];
      }

      return api.get(url, { params }).then((res) => {
        return res.data ?? [];
      });
    }
  });

  const chartData = useMemo(() => {
    const months = Array.from({ length: 13 }, (_, i) => ({
      month: dayjs()
        .subtract(12 - i, 'month')
        .format('MMM YY'),
      count: 0
    }));

    for (const order of query.data || []) {
      // Build orders use `completion_date`; all other order types use `complete_date`
      const dateStr =
        order.complete_date ?? order.completion_date ?? order.shipment_date;
      if (!dateStr) continue;
      const label = dayjs(dateStr).format('MMM YY');
      const entry = months.find((m) => m.month === label);
      if (entry) entry.count++;
    }

    return months;
  }, [query.data]);

  return (
    <Stack gap='xs'>
      <StylishText size='md'>{title}</StylishText>
      <Box>
        <LoadingOverlay visible={query.isLoading || query.isFetching} />
        <BarChart
          h={200}
          data={chartData}
          dataKey='month'
          series={[{ name: 'count', label: t`Completed`, color: 'blue.6' }]}
          withYAxis={false}
          yAxisProps={{ domain: [0, 'auto'] }}
        />
      </Box>
    </Stack>
  );
}

/**
 * Display a simple chart of the number of completed orders per month, for the last 12 months.
 */
export default function OrderHistoryWidget({
  modelType
}: {
  modelType: ModelType;
}): DashboardWidgetProps {
  const user = useUserState();

  const modelInfo = useMemo(() => {
    return ModelInformationDict[modelType];
  }, [modelType]);

  // Extract translated model labels
  const models = modelInfo.label_multiple();

  return {
    label: `${modelType}-history`,
    title: t`Completed ${models}`,
    description: t`Display number of completed ${models} per month`,
    minHeight: 2,
    minWidth: 3,
    modelType: modelType,
    icon: 'chart_bar',
    visible: () => user.hasViewPermission(modelType),
    render: () => (
      <OrderHistoryComponent
        modelType={modelType}
        title={t`Completed ${models}`}
      />
    )
  };
}
