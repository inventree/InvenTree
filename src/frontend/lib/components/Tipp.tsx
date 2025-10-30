import { Alert, Stack, Text } from '@mantine/core';
import { type JSX, useState } from 'react';
import { useGuideState } from '../../src/states/GuideState';

export function Tipp({ id }: Readonly<{ id: string }>): JSX.Element | null {
  const [dismissed, setDismissed] = useState<boolean>(false); // TODO: read from state / local storage
  const [getGuideBySlug] = useGuideState((state) => [state.getGuideBySlug]);

  if (dismissed) {
    return null;
  }

  const tip_data = getGuideBySlug(id);
  if (!tip_data) {
    return null;
  }
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
