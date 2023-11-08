import { Trans, t } from '@lingui/macro';
import { Alert, Badge, Stack, Text, Tooltip } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';

/**
 * Small badge to indicate that a feature is a placeholder.
 */
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

/**
 * Placeholder panel for use in a PanelGroup.
 */
export function PlaceholderPanel() {
  return (
    <Stack>
      <Alert
        color="teal"
        title={t`This panel is a placeholder.`}
        icon={<IconInfoCircle />}
      >
        <Text color="gray">This panel has not yet been implemented</Text>
      </Alert>
    </Stack>
  );
}
