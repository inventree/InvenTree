import { t } from '@lingui/macro';
import { Badge, Skeleton } from '@mantine/core';

import { isTrue } from '../../functions/conversion';

export function PassFailButton({
  value,
  passText,
  failText
}: Readonly<{
  value: any;
  passText?: string;
  failText?: string;
}>) {
  const v = isTrue(value);
  const pass = passText ?? t`Pass`;
  const fail = failText ?? t`Fail`;

  return (
    <Badge
      color={v ? 'lime.5' : 'red.6'}
      variant='filled'
      radius='lg'
      size='sm'
      style={{ maxWidth: '50px' }}
    >
      {v ? pass : fail}
    </Badge>
  );
}

export function YesNoButton({ value }: Readonly<{ value: any }>) {
  return <PassFailButton value={value} passText={t`Yes`} failText={t`No`} />;
}

export function YesNoUndefinedButton({ value }: Readonly<{ value?: boolean }>) {
  if (value === undefined) {
    return <Skeleton height={15} width={32} />;
  } else {
    return <YesNoButton value={value} />;
  }
}
