import { Group, LoadingOverlay, Paper, Text } from '@mantine/core';

import * as classes from '../../main.css';

export interface StatisticItemProps {
  title: string;
  value: string;
}

export function StatisticItem({
  id,
  data,
  isLoading
}: Readonly<{
  id: string;
  data: StatisticItemProps;
  isLoading: boolean;
}>) {
  return (
    <Paper withBorder p='xs' key={id} pos='relative'>
      <LoadingOverlay visible={isLoading} overlayProps={{ blur: 2 }} />
      <Group justify='space-between'>
        <Text size='xs' c='dimmed' className={classes.dashboardItemTitle}>
          {data.title}
        </Text>
      </Group>

      <Group align='flex-end' gap='xs' mt={25}>
        <Text className={classes.dashboardItemValue}>{data.value}</Text>
      </Group>
    </Paper>
  );
}
