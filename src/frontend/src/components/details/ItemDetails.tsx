import { Paper, SimpleGrid } from '@mantine/core';
import type React from 'react';
import { useMemo } from 'react';

import { DetailsTable, type DetailsTableProps } from './Details';

export type { DetailsTableProps };

export function ItemDetailsGrid({
  children,
  tables
}: React.PropsWithChildren<{ tables?: DetailsTableProps[] }>) {
  const visibleTables = useMemo(
    () => tables?.filter((t) => t.fields.some((f) => !f.hidden)) ?? [],
    [tables]
  );

  return (
    <Paper p='xs'>
      <SimpleGrid
        cols={{ base: 1, '900px': 2 }}
        type='container'
        spacing='xs'
        verticalSpacing='xs'
      >
        {children}
        {visibleTables.map((props, index) => (
          <DetailsTable key={index} {...props} />
        ))}
      </SimpleGrid>
    </Paper>
  );
}
