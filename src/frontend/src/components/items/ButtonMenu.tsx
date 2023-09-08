import { ActionIcon, Menu, Tooltip } from '@mantine/core';
import { Component } from 'react';

/**
 * A ButtonMenu is a button that opens a menu when clicked.
 * It features a number of actions, which can be selected by the user.
 */
export function ButtonMenu({
  icon,
  actions,
  tooltip = '',
  label = ''
}: {
  icon: any;
  actions: any[];
  label?: string;
  tooltip?: string;
}) {
  let idx = 0;

  return (
    <Menu shadow="xs">
      <Menu.Target>
        <ActionIcon>
          <Tooltip label={tooltip}>{icon}</Tooltip>
        </ActionIcon>
      </Menu.Target>
      <Menu.Dropdown>
        {label && <Menu.Label>{label}</Menu.Label>}
        {actions.map((action) => (
          <Menu.Item key={idx++}>{action}</Menu.Item>
        ))}
      </Menu.Dropdown>
    </Menu>
  );
}
