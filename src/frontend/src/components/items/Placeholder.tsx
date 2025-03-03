import { t } from '@lingui/macro';
import { Alert, Stack, Text } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';

/**
 * Placeholder panel for use in a PanelGroup.
 */
export function PlaceholderPanel() {
  return (
    <Stack>
      <Alert
        color='teal'
        title={t`This panel is a placeholder.`}
        icon={<IconInfoCircle />}
      >
        <Text c='gray'>This panel has not yet been implemented</Text>
      </Alert>
    </Stack>
  );
}
