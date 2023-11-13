import { t } from '@lingui/macro';
import { Badge } from '@mantine/core';

export function YesNoButton({ value }: { value: boolean }) {
  return (
    <Badge
      color={value ? 'lime.5' : 'red.6'}
      variant="filled"
      radius="lg"
      size="sm"
    >
      {value ? t`Yes` : t`No`}
    </Badge>
  );
}
