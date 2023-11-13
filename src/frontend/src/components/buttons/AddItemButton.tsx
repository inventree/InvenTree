import { IconPlus } from '@tabler/icons-react';

import { ActionButton, ActionButtonProps } from './ActionButton';

/**
 * A generic icon button which is used to add or create a new item
 */
export function AddItemButton(props: ActionButtonProps) {
  return <ActionButton {...props} color="green" icon={<IconPlus />} />;
}
