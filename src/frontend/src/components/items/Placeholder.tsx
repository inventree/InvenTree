import { Trans, t } from '@lingui/macro';
import { Badge, Tooltip } from '@mantine/core';

export function Placeholder() {
  return (
    <Tooltip
      multiline
      width={220}
      withArrow
      label={t`Use this button to save this information in your profile, after that you will be able to access it any time and share it via email.`}
    >
      <Badge color="teal" variant="outline">
        <Trans>PLH</Trans>
      </Badge>
    </Tooltip>
  );
}
