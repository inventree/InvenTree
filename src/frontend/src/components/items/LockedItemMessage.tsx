import { t } from '@lingui/core/macro';
import { Alert } from '@mantine/core';
import { IconLock } from '@tabler/icons-react';

export function LockedItemMessage() {
  return (
    <Alert color='yellow' icon={<IconLock />}>
      {t`This item is locked`}
    </Alert>
  );
}
