import { ActionIcon } from '@mantine/core';
import { IconEdit, IconDeviceFloppy } from '@tabler/icons-react';

export function EditButton(
  setEditing: (value?: React.SetStateAction<boolean> | undefined) => void,
  editing: boolean,
  disabled?: boolean
) {
  return (
    <ActionIcon onClick={() => setEditing()} disabled={disabled}>
      {editing ? <IconDeviceFloppy /> : <IconEdit />}
    </ActionIcon>
  );
}
