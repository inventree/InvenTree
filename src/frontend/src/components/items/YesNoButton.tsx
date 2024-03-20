import { t } from '@lingui/macro';
import { Badge } from '@mantine/core';

import { isTrue } from '../../functions/conversion';

export function PassFailButton({
  value,
  passText,
  failText
}: {
  value: any;
  passText?: string;
  failText?: string;
}) {
  const v = isTrue(value);
  const pass = passText || t`Pass`;
  const fail = failText || t`Fail`;

  return (
    <Badge
      color={v ? 'lime.5' : 'red.6'}
      variant="filled"
      radius="lg"
      size="sm"
    >
      {v ? pass : fail}
    </Badge>
  );
}

export function YesNoButton({ value }: { value: any }) {
  return <PassFailButton value={value} passText={t`Yes`} failText={t`No`} />;
}
