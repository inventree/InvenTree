import { Paper, SimpleGrid } from '@mantine/core';
import type React from 'react';

export function ItemDetailsGrid(props: React.PropsWithChildren<{}>) {
  return (
    <Paper p='xs'>
      <SimpleGrid cols={2} spacing='xs' verticalSpacing='xs'>
        {props.children}
      </SimpleGrid>
    </Paper>
  );
}
