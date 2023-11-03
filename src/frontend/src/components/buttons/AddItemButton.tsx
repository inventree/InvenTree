import { ActionIcon, Tooltip } from '@mantine/core';
import { IconPlus } from '@tabler/icons-react';

/**
 * A generic icon button which is used to add or create a new item
 */
export function AddItemButton({
  tooltip,
  callback,
  disabled = false
}: {
  tooltip: string;
  callback?: () => void;
  disabled?: boolean;
}) {
  return (
    <Tooltip key={tooltip} label={tooltip} disabled={!tooltip}>
      <ActionIcon
        disabled={disabled}
        radius="sm"
        onClick={() => {
          !disabled && callback && callback();
        }}
      >
        <IconPlus color="green" />
      </ActionIcon>
    </Tooltip>
  );
}
