import { Paper, SimpleGrid } from '@mantine/core';
import { useElementSize } from '@mantine/hooks';
import type React from 'react';
import { useMemo } from 'react';

export function ItemDetailsGrid(props: React.PropsWithChildren<{}>) {
  const { ref, width } = useElementSize();

  const cols = useMemo(() => (width > 700 ? 2 : 1), [width]);

  return (
    <Paper p='xs'>
      <SimpleGrid cols={cols} spacing='xs' verticalSpacing='xs' ref={ref}>
        {props.children}
      </SimpleGrid>
    </Paper>
  );
}
