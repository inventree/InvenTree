import { t } from '@lingui/macro';
import { Badge } from '@mantine/core';

export function YesNoButton(value: any) {
  const bool = value in ['true', true, 1, '1'];

  return (
    <Badge
      color={bool ? 'green' : 'red'}
      variant="filled"
      radius="lg"
      size="sm"
    >
      {bool ? t`Yes` : t`No`}
    </Badge>
  );
}
