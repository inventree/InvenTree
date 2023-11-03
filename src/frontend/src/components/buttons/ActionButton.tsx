import { ActionIcon, Group, Text, Tooltip } from '@mantine/core';
import { ReactNode } from 'react';

export type ActionButtonProps = {
  icon?: ReactNode;
  text?: string;
  color?: string;
  tooltip?: string;
  variant?: string;
  size?: number;
  disabled?: boolean;
  onClick?: any;
  hidden?: boolean;
};

/**
 * Construct a simple action button with consistent styling
 */
export function ActionButton(props: ActionButtonProps) {
  return (
    !props.hidden && (
      <ActionIcon
        key={props.text ?? props.tooltip}
        disabled={props.disabled}
        radius="xs"
        color={props.color}
        size={props.size}
        onClick={props.onClick}
      >
        <Tooltip
          disabled={!props.tooltip && !props.text}
          label={props.tooltip ?? props.text}
          position="left"
        >
          <Group spacing="xs" noWrap={true}>
            {props.icon}
            {props.text && <Text>{props.text}</Text>}
          </Group>
        </Tooltip>
      </ActionIcon>
    )
  );
}
