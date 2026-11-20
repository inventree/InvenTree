import { Group, Paper, Stack, Text } from '@mantine/core';
import type { ReactNode } from 'react';

import { StylishText } from '@lib/components/StylishText';

export function FactItem({
  title,
  value,
  action
}: Readonly<{ title: string; value: ReactNode; action?: ReactNode }>) {
  return (
    <Paper p='md' shadow='xs'>
      <Stack gap='xs'>
        <StylishText size='md'>{title}</StylishText>
        <Group justify='space-between' wrap='nowrap'>
          <Text>{value}</Text>
          {action}
        </Group>
      </Stack>
    </Paper>
  );
}
