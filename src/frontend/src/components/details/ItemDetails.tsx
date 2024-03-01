import { Paper, SimpleGrid } from '@mantine/core';
import React from 'react';

import { DetailImageButtonProps } from './DetailsImage';

export function ItemDetailsGrid(props: React.PropsWithChildren<{}>) {
  return (
    <Paper p="xs">
      <SimpleGrid cols={2} spacing="xs" verticalSpacing="xs">
        {props.children}
      </SimpleGrid>
    </Paper>
  );
}
