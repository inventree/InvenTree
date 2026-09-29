import { cancelEvent } from '@lib/functions/Events';
import { Box, Group, Loader } from '@mantine/core';
import { IconCornerDownRight } from '@tabler/icons-react';
import type { ReactNode } from 'react';
import RowExpansionIcon from './RowExpansionIcon';

// Indentation (in pixels) applied for each level of nesting
const NESTED_ROW_INDENT: number = 20;

/**
 * Cell wrapper for a table which displays nested (child) rows.
 *
 * - Indents the cell content according to the nesting depth
 * - Displays an icon to indicate that the row is a child of the row above
 * - Displays an expansion toggle for rows which can be expanded
 */
export default function NestedRowCell({
  depth,
  expandable,
  expanded,
  loading,
  onToggle,
  children
}: Readonly<{
  depth: number;
  expandable: boolean;
  expanded: boolean;
  loading: boolean;
  onToggle: () => void;
  children: ReactNode;
}>) {
  return (
    <Group
      gap='xs'
      wrap='nowrap'
      justify='left'
      style={{ paddingLeft: Math.max(0, depth - 1) * NESTED_ROW_INDENT }}
    >
      {depth > 0 && (
        <IconCornerDownRight
          size={16}
          color='var(--mantine-color-dimmed)'
          style={{ flexShrink: 0 }}
        />
      )}
      {expandable &&
        (loading ? (
          <Loader size='xs' aria-label='nested-row-loading' />
        ) : (
          <RowExpansionIcon
            enabled
            expanded={expanded}
            ariaLabel={expanded ? 'nested-row-collapse' : 'nested-row-expand'}
            onClick={(event: React.MouseEvent) => {
              cancelEvent(event);
              onToggle();
            }}
          />
        ))}
      <Box style={{ flex: 1, minWidth: 0 }}>{children}</Box>
    </Group>
  );
}
