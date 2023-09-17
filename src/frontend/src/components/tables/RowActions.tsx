import { t } from '@lingui/macro';
import { ActionIcon, Tooltip } from '@mantine/core';
import { Menu, Text } from '@mantine/core';
import { IconDots } from '@tabler/icons-react';
import { ReactNode } from 'react';

// Type definition for a table row action
export type RowAction = {
  title: string;
  color?: string;
  onClick: () => void;
  tooltip?: string;
  icon?: ReactNode;
};

/**
 * Component for displaying actions for a row in a table.
 * Displays a simple dropdown menu with a list of actions.
 */
export function RowActions({
  title,
  actions,
  disabled = false
}: {
  title?: string;
  disabled?: boolean;
  actions: RowAction[];
}): ReactNode {
  return (
    actions.length > 0 && (
      <Menu withinPortal={true} disabled={disabled}>
        <Menu.Target>
          <Tooltip label={title || t`Actions`}>
            <ActionIcon disabled={disabled} variant="subtle" color="gray">
              <IconDots />
            </ActionIcon>
          </Tooltip>
        </Menu.Target>
        <Menu.Dropdown>
          <Menu.Label>{title || t`Actions`}</Menu.Label>
          {actions.map((action, idx) => (
            <Menu.Item
              key={idx}
              onClick={action.onClick}
              icon={action.icon}
              title={action.tooltip || action.title}
            >
              <Text size="xs" color={action.color}>
                {action.title}
              </Text>
            </Menu.Item>
          ))}
        </Menu.Dropdown>
      </Menu>
    )
  );
}
