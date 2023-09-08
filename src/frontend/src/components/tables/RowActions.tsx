import { t } from '@lingui/macro';
import { ActionIcon } from '@mantine/core';
import { Menu } from '@mantine/core';
import { IconDots } from '@tabler/icons-react';
import { ReactNode } from 'react';

// Type definition for a table row action
export type RowAction = {
  title: string;
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
  actions
}: {
  title?: string;
  actions: RowAction[];
}): ReactNode {
  return (
    <Menu>
      <Menu.Target>
        <ActionIcon variant="subtle" color="gray">
          <IconDots />
        </ActionIcon>
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
            {action.title}
          </Menu.Item>
        ))}
      </Menu.Dropdown>
    </Menu>
  );
}
