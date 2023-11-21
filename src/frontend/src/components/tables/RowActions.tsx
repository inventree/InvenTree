import { t } from '@lingui/macro';
import { ActionIcon, Group, Tooltip } from '@mantine/core';
import { Menu } from '@mantine/core';
import { IconCopy, IconDots, IconEdit, IconTrash } from '@tabler/icons-react';
import { ReactNode, useMemo, useState } from 'react';

import { notYetImplemented } from '../../functions/notifications';

// Type definition for a table row action
export type RowAction = {
  title: string;
  color?: string;
  icon: ReactNode;
  onClick?: () => void;
  hidden?: boolean;
};

// Component for duplicating a row in a table
export function RowDuplicateAction({
  onClick,
  hidden
}: {
  onClick?: () => void;
  hidden?: boolean;
}): RowAction {
  return {
    title: t`Duplicate`,
    color: 'green',
    onClick: onClick,
    icon: <IconCopy />,
    hidden: hidden
  };
}

// Component for editing a row in a table
export function RowEditAction({
  onClick,
  hidden
}: {
  onClick?: () => void;
  hidden?: boolean;
}): RowAction {
  return {
    title: t`Edit`,
    color: 'blue',
    onClick: onClick,
    icon: <IconEdit />,
    hidden: hidden
  };
}

// Component for deleting a row in a table
export function RowDeleteAction({
  onClick,
  hidden
}: {
  onClick?: () => void;
  hidden?: boolean;
}): RowAction {
  return {
    title: t`Delete`,
    color: 'red',
    onClick: onClick,
    icon: <IconTrash />,
    hidden: hidden
  };
}

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
  // Prevent default event handling
  // Ref: https://icflorescu.github.io/mantine-datatable/examples/links-or-buttons-inside-clickable-rows-or-cells
  function openMenu(event: any) {
    event?.preventDefault();
    event?.stopPropagation();
    event?.nativeEvent?.stopImmediatePropagation();
    setOpened(!opened);
  }

  const [opened, setOpened] = useState(false);

  const visibleActions = useMemo(() => {
    return actions.filter((action) => !action.hidden);
  }, [actions]);

  // Render a single action icon
  function RowActionIcon(action: RowAction) {
    return (
      <Tooltip withinPortal={true} label={action.title} key={action.title}>
        <ActionIcon
          color={action.color}
          size={20}
          onClick={(event) => {
            // Prevent clicking on the action from selecting the row itself
            event?.preventDefault();
            event?.stopPropagation();
            event?.nativeEvent?.stopImmediatePropagation();

            if (action.onClick) {
              action.onClick();
            } else {
              notYetImplemented();
            }

            setOpened(false);
          }}
        >
          {action.icon}
        </ActionIcon>
      </Tooltip>
    );
  }

  // If only a single action is available, display that
  if (visibleActions.length == 1) {
    return <RowActionIcon {...visibleActions[0]} />;
  }

  return (
    visibleActions.length > 0 && (
      <Menu
        withinPortal={true}
        disabled={disabled}
        position="left"
        opened={opened}
        onChange={setOpened}
      >
        <Menu.Target>
          <Tooltip withinPortal={true} label={title || t`Actions`}>
            <ActionIcon
              onClick={openMenu}
              disabled={disabled}
              variant="subtle"
              color="gray"
            >
              <IconDots />
            </ActionIcon>
          </Tooltip>
        </Menu.Target>
        <Menu.Dropdown>
          <Group position="right" spacing="xs" p={8}>
            {visibleActions.map((action) => (
              <RowActionIcon key={action.title} {...action} />
            ))}
          </Group>
        </Menu.Dropdown>
      </Menu>
    )
  );
}
