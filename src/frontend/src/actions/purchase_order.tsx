import { t } from '@lingui/macro';
import { IconBasketCheck } from '@tabler/icons-react';

import { ActionType } from '.';
import { notYetImplemented } from '../functions/notifications';

export const purchase_orderActions: ActionType[] = [
  {
    title: t`Receive order`,
    function: notYetImplemented,
    icon: <IconBasketCheck />
  }
];
