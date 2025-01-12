import { Paper, SimpleGrid } from '@mantine/core';
import type React from 'react';

export function ItemDetailsGrid(props: React.PropsWithChildren<{}>) {
  return (
    <Paper p='xs'>
      <SimpleGrid
        cols={{ base: 1, '750px': 2 }}
        type='container'
        spacing='xs'
        verticalSpacing='xs'
      >
        {props.children}
      </SimpleGrid>
    </Paper>
  );
}
