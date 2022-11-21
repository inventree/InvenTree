import { createStyles, LoadingOverlay, Group, Paper, Text } from '@mantine/core';

const useStyles = createStyles((theme) => ({
  value: {
    fontSize: 24,
    fontWeight: 700,
    lineHeight: 1,
  },

  title: {
    fontWeight: 700,
  },
}));

export interface StatisticItemProps {title: string; value: string;}

export function StatisticItem({ id, data, isLoading }: {id: string, data: StatisticItemProps, isLoading: boolean}) {
  const { classes } = useStyles();

  return (
    <Paper withBorder p="xs" radius="md" key={id} pos="relative">
      <LoadingOverlay visible={isLoading} overlayBlur={2} />
      <Group position="apart">
        <Text size="xs" color="dimmed" className={classes.title}>
          {data.title}
        </Text>
      </Group>

      <Group align="flex-end" spacing="xs" mt={25}>
        <Text className={classes.value}>{data.value}</Text>
      </Group>
    </Paper>
  );
}
