import { t } from '@lingui/macro';
import { IconNumber } from '@tabler/icons-react';

import { notYetImplemented } from '../functions/notifications';

const dummyCountAction = {
  title: t`count`,
  function: notYetImplemented,
  icon: <IconNumber />
};

export const dummyDefaultActions = [dummyCountAction];
