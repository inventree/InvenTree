import { t } from '@lingui/macro';
import { Divider, Group, HoverCard, Stack, Text } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';
import { ReactNode, useMemo } from 'react';

import { InvenTreeIcon, InvenTreeIconType } from '../functions/icons';

/*
 * A custom hovercard element for displaying extra information in a table cell.
 * If a table cell has extra information available,
 * it can be displayed as a drop-down hovercard when the user hovers over the cell.
 */
export function TableHoverCard({
  value, // The value of the cell
  extra, // The extra information to display
  title, // The title of the hovercard
  icon, // The icon to display
  iconColor // The icon color
}: {
  value: any;
  extra?: ReactNode;
  title?: string;
  icon?: InvenTreeIconType;
  iconColor?: string;
}) {
  const extraItems: ReactNode = useMemo(() => {
    if (Array.isArray(extra)) {
      if (extra.length == 0) {
        return null;
      }

      return (
        <Stack gap="xs">
          {extra.map((item, idx) => (
            <div key={`item-${idx}`}>{item}</div>
          ))}
        </Stack>
      );
    } else {
      return extra;
    }
  }, [extra]);

  // If no extra information presented, just return the raw value
  if (!extraItems) {
    return value;
  }

  return (
    <HoverCard withinPortal={true} closeDelay={20} openDelay={250}>
      <HoverCard.Target>
        <Group gap="xs" justify="space-between" wrap="nowrap">
          {value}
          <InvenTreeIcon
            icon={icon ?? 'info'}
            iconProps={{ size: 16, color: iconColor ?? 'blue' }}
          />
        </Group>
      </HoverCard.Target>
      <HoverCard.Dropdown>
        <Stack gap="xs">
          <Group gap="xs" justify="left">
            <IconInfoCircle size="16" color="blue" />
            <Text fw="bold">{title}</Text>
          </Group>
          <Divider />
          {extraItems}
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
