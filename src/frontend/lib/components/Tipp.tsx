import { Alert, Stack, Text } from '@mantine/core';
import { type JSX, useState } from 'react';
import { globalTipps } from '../../src/pages/Index/Settings/AdminCenter/HomePanel';

export function Tipp({ id }: Readonly<{ id: string }>): JSX.Element | null {
  const [dismissed, setDismissed] = useState<boolean>(false); // TODO: read from state / local storage

  if (dismissed) {
    return null;
  }

  const tip_data = globalTipps[id];
  return (
    <Alert
      color={tip_data.color}
      title={tip_data.title}
      withCloseButton
      onClose={() => setDismissed(true)}
    >
      <Stack gap='xs'>
        <Text>{tip_data.text}</Text>
      </Stack>
    </Alert>
  );
}
