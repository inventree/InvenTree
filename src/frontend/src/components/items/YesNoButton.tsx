import { t } from '@lingui/macro';
import { Badge } from '@mantine/core';

export function YesNoButton({ value }: { value: any }) {
  const bool =
    String(value).toLowerCase().trim() in ['true', '1', 't', 'y', 'yes'];

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
