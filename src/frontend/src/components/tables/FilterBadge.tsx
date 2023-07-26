import { t } from '@lingui/macro';
import { Badge, CloseButton } from '@mantine/core';
import { Text, Tooltip } from '@mantine/core';
import { Group } from '@mantine/core';

import { TableFilter } from './Filter';

export function FilterBadge({
  filter,
  onFilterRemove
}: {
  filter: TableFilter;
  onFilterRemove: () => void;
}) {
  /**
   * Construct text to display for the given badge ID
   */
  function filterDescription() {
    let text = filter.label || filter.name;

    text += ' = ';
    text += filter.value;

    return text;
  }

  return (
    <Badge
      size="lg"
      radius="lg"
      variant="outline"
      color="gray"
      styles={(theme) => ({
        root: {
          paddingRight: '4px'
        },
        inner: {
          textTransform: 'none'
        }
      })}
    >
      <Group spacing={1}>
        <Text>{filterDescription()}</Text>
        <Tooltip label={t`Remove filter`}>
          <CloseButton color="red" onClick={() => onFilterRemove()} />
        </Tooltip>
      </Group>
    </Badge>
  );
}
