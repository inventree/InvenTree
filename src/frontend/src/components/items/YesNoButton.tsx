import { t } from '@lingui/macro';
import { Badge } from '@mantine/core';

import { isTrue } from '../../functions/conversion';

export function YesNoButton({ value }: { value: any }) {
  const v = isTrue(value);

  return (
    <Badge
      color={v ? 'lime.5' : 'red.6'}
      variant="filled"
      radius="lg"
      size="sm"
    >
      {v ? t`Yes` : t`No`}
    </Badge>
  );
}
