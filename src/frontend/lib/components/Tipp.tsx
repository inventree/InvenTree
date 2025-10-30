import type { TippData } from '@lib/types/Core';
import { Alert, Stack, Text } from '@mantine/core';
import { type JSX, useMemo, useState } from 'react';
import { useGuideState } from '../../src/states/GuideState';

export function Tipp({ id }: Readonly<{ id: string }>): JSX.Element {
  const [dismissed, setDismissed] = useState<boolean>(false); // TODO: read from state / local storage
  const { getGuideBySlug } = useGuideState();
  const tip = useMemo(() => getGuideBySlug(id), [id]);

  if (!tip || dismissed) {
    return <></>;
  }
  const tip_data: TippData = tip.guide_data;
  return (
    <Alert
      color={tip_data.color}
      title={tip_data.title}
      withCloseButton
      onClose={() => setDismissed(true)}
    >
      <Stack gap='xs'>
        <Text>{tip_data.detail_text}</Text>
      </Stack>
    </Alert>
  );
}
