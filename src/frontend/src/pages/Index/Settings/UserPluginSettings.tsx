import { t } from '@lingui/core/macro';
import { Alert, Stack, Text } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';

export default function UserPluginSettings() {
  return (
    <Stack gap='xs'>
      <Alert color='blue' icon={<IconInfoCircle />}>
        <Text>{t`Configuration for plugins which require user specific settings`}</Text>
      </Alert>
    </Stack>
  );
}
