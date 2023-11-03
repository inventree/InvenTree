import { Divider, Group, HoverCard, Stack, Text } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';

/*
 * A custom hovercard element for displaying extra information in a table cell.
 * If a table cell has extra information available,
 * it can be displayed as a drop-down hovercard when the user hovers over the cell.
 */
export function TableHoverCard({
  value, // The value of the cell
  extra, // The extra information to display
  title // The title of the hovercard
}: {
  value: any;
  extra?: any;
  title?: string;
}) {
  // If no extra information presented, just return the raw value
  if (!extra) {
    return value;
  }

  return (
    <HoverCard>
      <HoverCard.Target>
        <Group spacing="xs" position="apart" noWrap={true}>
          {value}
          <IconInfoCircle size="16" color="blue" />
        </Group>
      </HoverCard.Target>
      <HoverCard.Dropdown>
        <Stack spacing="xs">
          <Group spacing="xs" position="left">
            <IconInfoCircle size="16" color="blue" />
            <Text weight="bold">{title}</Text>
          </Group>
          <Divider />
          {extra}
        </Stack>
      </HoverCard.Dropdown>
    </HoverCard>
  );
}
