import { t } from '@lingui/core/macro';
import { Badge, Group, Text, Tooltip } from '@mantine/core';
import type { ReactNode } from 'react';

import { formatPriceRange } from '../../defaults/formatters';

/**
 * Render a (min - max) cost range, with an optional "incomplete" badge.
 *
 * Used for both the StockItemCost summary and individual StockItemCostEntry records.
 * Note: An estimated cost is recorded as a range, which is displayed as "min - max".
 */
export function RenderCostRange({
  minCost,
  maxCost,
  currency,
  multiplier = 1,
  incomplete = false
}: Readonly<{
  minCost: number | string | null | undefined;
  maxCost: number | string | null | undefined;
  currency?: string;
  multiplier?: number;
  incomplete?: boolean;
}>): ReactNode {
  const scale = (value: number | string | null | undefined) =>
    value === null || value === undefined || value === ''
      ? null
      : Number(value) * multiplier;

  return (
    <Group gap='xs' wrap='nowrap'>
      <Text size='sm'>
        {formatPriceRange(scale(minCost), scale(maxCost), {
          currency: currency
        })}
      </Text>
      {incomplete && (
        <Tooltip
          label={t`One or more costs could not be included (e.g. no exchange rate available)`}
        >
          <Badge color='orange' size='xs' variant='light'>
            {t`Incomplete`}
          </Badge>
        </Tooltip>
      )}
    </Group>
  );
}
