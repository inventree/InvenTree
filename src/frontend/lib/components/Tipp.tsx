import type { TippData } from '@lib/types/Core';
import { Alert, Button, Group, Stack, Text } from '@mantine/core';
import { IconExternalLink } from '@tabler/icons-react';
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
        {tip_data.links && tip_data.links.length > 0 && (
          <Group gap='xs'>
            {tip_data.links.map((link, index) => (
              <Button
                rightSection={<IconExternalLink />}
                size='sm'
                variant='light'
                key={index}
                component='a'
                href={link[1]}
                target='_blank'
                rel='noopener noreferrer'
              >
                {link[0]}
              </Button>
            ))}
          </Group>
        )}
      </Stack>
    </Alert>
  );
}
