import { IconPlus } from '@tabler/icons-react';

import {
  ActionButton,
  type ActionButtonProps
} from '@lib/components/buttons/ActionButton';

/**
 * A generic icon button which is used to add or create a new item
 */
export function AddItemButton(props: Readonly<ActionButtonProps>) {
  return <ActionButton {...props} color='green' icon={<IconPlus />} />;
}
