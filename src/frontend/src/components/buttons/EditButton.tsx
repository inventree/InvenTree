import { ActionIcon } from '@mantine/core';
import { IconDeviceFloppy, IconEdit } from '@tabler/icons-react';

export function EditButton({
  setEditing,
  editing,
  disabled,
  saveIcon
}: Readonly<{
  setEditing: (value?: React.SetStateAction<boolean> | undefined) => void;
  editing: boolean;
  disabled?: boolean;
  saveIcon?: JSX.Element;
}>) {
  saveIcon = saveIcon || <IconDeviceFloppy />;
  return (
    <ActionIcon
      onClick={() => setEditing()}
      disabled={disabled}
      variant='default'
    >
      {editing ? saveIcon : <IconEdit />}
    </ActionIcon>
  );
}
