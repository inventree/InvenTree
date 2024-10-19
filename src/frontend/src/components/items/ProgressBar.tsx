import { Progress, Stack, Text } from '@mantine/core';
import { useMemo } from 'react';

export type ProgressBarProps = {
  value: number;
  maximum?: number;
  label?: string;
  progressLabel?: boolean;
  size?: string;
};

/**
 * A progress bar element, built on mantine.Progress
 * The color of the bar is determined based on the value
 */
export function ProgressBar(props: Readonly<ProgressBarProps>) {
  const progress = useMemo(() => {
    const maximum = props.maximum ?? 100;
    const value = Math.max(props.value, 0);

    if (maximum == 0) {
      return 0;
    }

    return (value / maximum) * 100;
  }, [props]);

  return (
    <Stack gap={2} style={{ flexGrow: 1, minWidth: '100px' }}>
      {props.progressLabel && (
        <Text ta='center' size='xs'>
          {props.value} / {props.maximum}
        </Text>
      )}
      <Progress
        value={progress}
        color={progress < 100 ? 'orange' : progress > 100 ? 'blue' : 'green'}
        size={props.size ?? 'md'}
        radius='sm'
      />
    </Stack>
  );
}
