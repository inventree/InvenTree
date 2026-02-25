import { ActionIcon, Menu, Tooltip } from '@mantine/core';

/**
 * A ButtonMenu is a button that opens a menu when clicked.
 * It features a number of actions, which can be selected by the user.
 */
export function ButtonMenu({
  icon,
  actions,
  tooltip = '',
  label = ''
}: Readonly<{
  icon: any;
  actions: React.ReactNode[];
  label?: string;
  tooltip?: string;
}>) {
  return (
    <Menu shadow='xs'>
      <Menu.Target>
        <ActionIcon variant='default'>
          <Tooltip label={tooltip}>{icon}</Tooltip>
        </ActionIcon>
      </Menu.Target>
      <Menu.Dropdown>
        {label && <Menu.Label>{label}</Menu.Label>}
        {actions.map((action, i) => (
          <Menu.Item key={`${i}-${action}`}>{action}</Menu.Item>
        ))}
      </Menu.Dropdown>
    </Menu>
  );
}
