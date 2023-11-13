import { t } from '@lingui/macro';
import { Divider, Group, HoverCard, Stack, Text } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';
import { ReactNode } from 'react';

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
  extra?: ReactNode;
  title?: string;
}) {
  // If no extra information presented, just return the raw value
  if (!extra) {
    return value;
  }

  if (Array.isArray(extra) && extra.length == 0) {
    return value;
  }

  return (
    <HoverCard withinPortal={true}>
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

/**
 * Custom hovercard for displaying projectcode detail in a table
 */
export function ProjectCodeHoverCard({ projectCode }: { projectCode: any }) {
  return projectCode ? (
    <TableHoverCard
      value={projectCode?.code}
      title={t`Project Code`}
      extra={
        projectCode && (
          <Text key="project-code">{projectCode?.description}</Text>
        )
      }
    />
  ) : (
    '-'
  );
}
