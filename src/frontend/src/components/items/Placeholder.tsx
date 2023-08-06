import { Trans, t } from '@lingui/macro';
import { Badge, Tooltip } from '@mantine/core';

export function PlaceholderPill() {
  return (
    <Tooltip
      multiline
      width={220}
      withArrow
      label={t`This feature/button/site is a placeholder for a feature that is not implemented, only partial or intended for testing.`}
    >
      <Badge color="teal" variant="outline">
        <Trans>PLH</Trans>
      </Badge>
    </Tooltip>
  );
}
