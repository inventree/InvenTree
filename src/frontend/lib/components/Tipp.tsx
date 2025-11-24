import type { TippData } from '@lib/types/Core';
import { Alert, Stack, Text } from '@mantine/core';
import { type JSX, useMemo, useState } from 'react';
import { useGuideState } from '../../src/states/GuideState';

export function Tipp({ id }: Readonly<{ id: string }>): JSX.Element {
  const { getGuideBySlug, closeGuide } = useGuideState();
  const [val, setVal] = useState(0); // Force re-render on close
  const tip = useMemo(() => getGuideBySlug(id), [id, val]);

  if (!tip) {
    return <></>;
  }
  const tip_data: TippData = tip.guide_data;
  if (tip.is_applicable === false) {
    return <></>;
  }

  return (
    <Alert
      color={tip_data.color}
      title={tip_data.title}
      withCloseButton
      onClose={async () => {
        await closeGuide(id);
        setVal(val + 1);
      }}
    >
      <Stack gap='xs'>
        <Text>{tip_data.detail_text}</Text>
      </Stack>
    </Alert>
  );
}
