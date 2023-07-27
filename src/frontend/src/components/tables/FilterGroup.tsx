import { t } from '@lingui/macro';
import { ActionIcon, Group, Text, Tooltip } from '@mantine/core';
import { IconFilterMinus } from '@tabler/icons-react';
import { IconFilterPlus } from '@tabler/icons-react';

import { TableFilter } from './Filter';
import { FilterBadge } from './FilterBadge';

/**
 * Return a table filter group component:
 * - Displays a list of active filters for the table
 * - Allows the user to add/remove filters
 * - Allows the user to clear all filters
 */
export function FilterGroup({
  activeFilters,
  onFilterAdd,
  onFilterRemove,
  onFilterClearAll
}: {
  activeFilters: TableFilter[];
  onFilterAdd: () => void;
  onFilterRemove: (filterName: string) => void;
  onFilterClearAll: () => void;
}) {
  return (
    <Group position="right" spacing={5}>
      {activeFilters.length == 0 && (
        <Text italic={true} size="sm">{t`Add table filter`}</Text>
      )}
      {activeFilters.map((f) => (
        <FilterBadge
          key={f.name}
          filter={f}
          onFilterRemove={() => onFilterRemove(f.name)}
        />
      ))}
      {activeFilters.length && (
        <ActionIcon
          radius="sm"
          variant="outline"
          onClick={() => onFilterClearAll()}
        >
          <Tooltip label={t`Clear all filters`}>
            <IconFilterMinus color="red" />
          </Tooltip>
        </ActionIcon>
      )}
      {
        <ActionIcon radius="sm" variant="outline" onClick={() => onFilterAdd()}>
          <Tooltip label={t`Add filter`}>
            <IconFilterPlus color="green" />
          </Tooltip>
        </ActionIcon>
      }
    </Group>
  );
}
