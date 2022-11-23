import { ActionIcon } from '@mantine/core';
import { IconEdit, IconDeviceFloppy } from '@tabler/icons';

export function EditButton(setEditing: () => void, editing: boolean) {
    return <ActionIcon onClick={() => setEditing()}>
        {editing ? <IconDeviceFloppy /> : <IconEdit />}
    </ActionIcon>;
}
