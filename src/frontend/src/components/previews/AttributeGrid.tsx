import { Divider, Table, Title } from '@mantine/core';
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
      <Table striped withRowBorders={false} fz='sm'>
        <Table.Tbody>
          {valid.map((item) => (
            <Table.Tr key={item.label}>
              <Table.Td w='50%' fw='bold'>
                {item.label}
              </Table.Td>
              <Table.Td w='50%'>{item.value}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </>
  );
}
