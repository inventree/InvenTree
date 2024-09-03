import { SimpleGrid } from '@mantine/core';

import { FactItem } from './FactItem';

export function FactCollection({
  items,
  minItems = 3
}: {
  items: { title: string; value: any }[];
  minItems?: number;
}) {
  return (
    <SimpleGrid cols={minItems} spacing="xs">
      {items.map((item, index) => (
        <FactItem key={index} title={item.title} value={item.value} />
      ))}
    </SimpleGrid>
  );
}
