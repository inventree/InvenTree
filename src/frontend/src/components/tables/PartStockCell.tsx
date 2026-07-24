import { t } from '@lingui/core/macro';
import { Group, Text } from '@mantine/core';
import type { ReactNode } from 'react';
import { formatDecimal } from '../../defaults/formatters';
import { TableHoverCard } from './TableHoverCard';

export function renderPartStockCell(record: any): ReactNode {
  if (record.virtual) {
    return (
      <Text size='sm' c='dimmed' fs='italic'>
        {t`Virtual part`}
      </Text>
    );
  }

  const extra: ReactNode[] = [];

  const stock = record?.total_in_stock ?? 0;
  const allocated =
    (record?.allocated_to_build_orders ?? 0) +
    (record?.allocated_to_sales_orders ?? 0);
  const available = Math.max(0, stock - allocated);
  const min_stock = record?.minimum_stock ?? 0;
  const max_stock = record?.maximum_stock ?? 0;

  let text = String(formatDecimal(stock));

  let color: string | undefined;

  if (min_stock > stock) {
    extra.push(
      <Text key='min-stock' c='orange'>
        {`${t`Minimum stock`}: ${formatDecimal(min_stock)}`}
      </Text>
    );

    color = 'orange';
  }

  if (max_stock > 0 && stock > max_stock) {
    extra.push(
      <Text key='max-stock' c='teal'>
        {`${t`Maximum stock`}: ${formatDecimal(max_stock)}`}
      </Text>
    );
  }

  if (record.ordering > 0) {
    extra.push(
      <Text key='on-order'>{`${t`On Order`}: ${formatDecimal(record.ordering)}`}</Text>
    );
  }

  if (record.building) {
    extra.push(
      <Text key='building'>{`${t`Building`}: ${formatDecimal(record.building)}`}</Text>
    );
  }

  if (record.allocated_to_build_orders > 0) {
    extra.push(
      <Text key='bo-allocations'>
        {`${t`Build Order Allocations`}: ${formatDecimal(record.allocated_to_build_orders)}`}
      </Text>
    );
  }

  if (record.allocated_to_sales_orders > 0) {
    extra.push(
      <Text key='so-allocations'>
        {`${t`Sales Order Allocations`}: ${formatDecimal(record.allocated_to_sales_orders)}`}
      </Text>
    );
  }

  if (available != stock) {
    extra.push(
      <Text key='available'>
        {t`Available`}: {formatDecimal(available)}
      </Text>
    );
  }

  if (record.external_stock > 0) {
    extra.push(
      <Text key='external'>
        {t`External stock`}: {formatDecimal(record.external_stock)}
      </Text>
    );
  }

  if ((record.variant_stock ?? 0) > 0) {
    extra.push(
      <Text key='variant-stock' size='sm'>
        {t`Includes variant stock`}: {formatDecimal(record.variant_stock)}
      </Text>
    );
    extra.push(
      <Text key='direct-stock' size='sm'>
        {t`Direct stock`}: {formatDecimal(record.in_stock ?? 0)}
      </Text>
    );
  }

  if (stock <= 0) {
    color = 'red';
    text = t`No stock`;
  } else if (available <= 0) {
    color = 'orange';
  } else if (available < min_stock) {
    color = 'yellow';
  }

  return (
    <TableHoverCard
      value={
        <Group gap='xs' justify='left' wrap='nowrap'>
          <Text c={color} size='sm'>
            {text}
          </Text>
          {record.units && (
            <Text size='xs' c={color}>
              [{record.units}]
            </Text>
          )}
        </Group>
      }
      title={t`Stock Information`}
      extra={extra}
    />
  );
}
