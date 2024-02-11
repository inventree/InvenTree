import { Group, LoadingOverlay, Paper, Text } from '@mantine/core';

import { InvenTreeStyle } from '../../globalStyle';

export interface StatisticItemProps {
  title: string;
  value: string;
}

export function StatisticItem({
  id,
  data,
  isLoading
}: {
  id: string;
  data: StatisticItemProps;
  isLoading: boolean;
}) {
  const { classes } = InvenTreeStyle();

  return (
    <Paper withBorder p="xs" key={id} pos="relative">
      <LoadingOverlay visible={isLoading} overlayBlur={2} />
      <Group position="apart">
        <Text size="xs" color="dimmed" className={classes.dashboardItemTitle}>
          {data.title}
        </Text>
      </Group>

      <Group align="flex-end" spacing="xs" mt={25}>
        <Text className={classes.dashboardItemValue}>{data.value}</Text>
      </Group>
    </Paper>
  );
}
