import { t } from '@lingui/macro';
import {
  ActionIcon,
  Chip,
  CloseButton,
  Group,
  Indicator,
  Space,
  Text,
  Tooltip
} from '@mantine/core';
import { IconMinus, IconPlus, IconTrash } from '@tabler/icons-react';

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
  availableFilters,
  onFilterAdd,
  onFilterRemove,
  onFilterClearAll
}: {
  activeFilters: TableFilter[];
  availableFilters: TableFilter[];
  onFilterAdd: () => void;
  onFilterRemove: (filterName: string) => void;
  onFilterClearAll: () => void;
}) {
  return (
    <Group position="right" spacing="xs">
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
        <ActionIcon variant="outline" onClick={() => onFilterClearAll()}>
          <Tooltip label={t`Clear all filters`}>
            <IconTrash color="red" />
          </Tooltip>
        </ActionIcon>
      )}
      {
        <ActionIcon variant="outline" onClick={() => onFilterAdd()}>
          <Tooltip label={t`Add filter`}>
            <IconPlus color="green" />
          </Tooltip>
        </ActionIcon>
      }
    </Group>
  );
}
