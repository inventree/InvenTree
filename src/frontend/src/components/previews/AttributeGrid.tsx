import { Divider, SimpleGrid, Text, Title } from '@mantine/core';
import type { ReactNode } from 'react';

export interface AttributeRow {
  label: string;
  value: ReactNode | null | undefined;
}

export function AttributeGrid({
  title,
  items
}: Readonly<{
  title: string;
  items: AttributeRow[];
}>) {
  const valid = items.filter(
    (item) => item.value !== null && item.value !== undefined
  );

  if (valid.length === 0) return null;

  return (
    <>
      <Divider />
      <Title order={4}>{title}</Title>
      <SimpleGrid cols={2} spacing='xs'>
        {valid.map((item) => (
          <>
            <Text key={`${item.label}-label`} fw={'bold'} size='sm'>
              {item.label}
            </Text>
            <Text key={`${item.label}-value`} size='sm'>
              {item.value}
            </Text>
          </>
        ))}
      </SimpleGrid>
    </>
  );
}
