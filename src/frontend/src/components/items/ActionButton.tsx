import { ActionIcon, Tooltip } from '@mantine/core';

/**
 * Construct a simple action button with consistent styling
 */
export function ActionButton({
  icon,
  color = 'black',
  tooltip = '',
  disabled = false,
  size = 18,
  onClick
}: {
  icon: any;
  color?: string;
  tooltip?: string;
  variant?: string;
  size?: number;
  disabled?: boolean;
  onClick?: any;
}) {
  return (
    <ActionIcon
      disabled={disabled}
      radius="xs"
      color={color}
      size={size}
      onClick={onClick}
    >
      <Tooltip disabled={!tooltip} label={tooltip} position="left">
        {icon}
      </Tooltip>
    </ActionIcon>
  );
}
