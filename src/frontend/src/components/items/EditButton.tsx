import { ActionIcon } from '@mantine/core';
import { IconDeviceFloppy, IconEdit } from '@tabler/icons-react';

export function EditButton(
  setEditing: (value?: React.SetStateAction<boolean> | undefined) => void,
  editing: boolean,
  disabled?: boolean
) {
  return (
    <ActionIcon onClick={() => setEditing()} radius="xs" color="green" variant="outline" disabled={disabled} size={18}>
      {editing ? <IconDeviceFloppy /> : <IconEdit />}
    </ActionIcon>
  );
}
