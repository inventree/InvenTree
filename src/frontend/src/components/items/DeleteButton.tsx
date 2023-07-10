import { ActionIcon } from '@mantine/core';
import { IconTrashFilled } from '@tabler/icons-react';

export function DeleteButton(
  disabled?: boolean,
  variant: string = "outline"
) {
  return (
    <ActionIcon disabled={disabled} radius="xs" color="red" variant={variant} size={18}>
      {<IconTrashFilled />}
    </ActionIcon>
  );
}
