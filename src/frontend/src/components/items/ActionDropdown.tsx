import { ActionIcon, Menu, Tooltip } from '@mantine/core';
import { ReactNode, useMemo } from 'react';

import { notYetImplemented } from '../../functions/notifications';

export type ActionDropdownItem = {
  icon: ReactNode;
  name: string;
  tooltip?: string;
  disabled?: boolean;
  onClick?: () => void;
};

/**
 * A simple Menu component which renders a set of actions.
 *
 * If no "active" actions are provided, the menu will not be rendered
 */
export function ActionDropdown({
  icon,
  tooltip,
  actions
}: {
  icon: ReactNode;
  tooltip?: string;
  actions: ActionDropdownItem[];
}) {
  const hasActions = useMemo(() => {
    return actions.some((action) => !action.disabled);
  }, [actions]);

  return hasActions ? (
    <Menu position="bottom-end">
      <Menu.Target>
        <Tooltip label={tooltip}>
          <ActionIcon size="lg" radius="sm" variant="outline">
            {icon}
          </ActionIcon>
        </Tooltip>
      </Menu.Target>
      <Menu.Dropdown>
        {actions.map((action) =>
          action.disabled ? null : (
            <Tooltip label={action.tooltip} key={`tooltip-${action.name}`}>
              <Menu.Item
                icon={action.icon}
                key={action.name}
                onClick={() => {
                  if (action.onClick != undefined) {
                    action.onClick();
                  } else {
                    notYetImplemented();
                  }
                }}
                disabled={action.disabled}
              >
                {action.name}
              </Menu.Item>
            </Tooltip>
          )
        )}
      </Menu.Dropdown>
    </Menu>
  ) : null;
}
