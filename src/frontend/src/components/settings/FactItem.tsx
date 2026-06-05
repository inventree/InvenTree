import { Paper, Stack, Text } from '@mantine/core';

import { StylishText } from '@lib/components/StylishText';

export function FactItem({
  title,
  value
}: Readonly<{ title: string; value: number }>) {
  return (
    <Paper p='md' shadow='xs'>
      <Stack gap='xs'>
        <StylishText size='md'>{title}</StylishText>
        <Text>{value}</Text>
      </Stack>
    </Paper>
  );
}
