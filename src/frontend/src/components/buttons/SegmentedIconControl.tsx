import {
  ActionIcon,
  type MantineColor,
  type MantineSize,
  SegmentedControl,
  Tooltip
} from '@mantine/core';
import type { ReactNode } from 'react';

export type SegmentedIconControlItem = {
  label: string;
  value: string;
  icon: ReactNode;
};

export default function SegmentedIconControl({
  data,
  value,
  size = 'sm',
  color,
  onChange
}: {
  data: SegmentedIconControlItem[];
  value: string;
  size?: MantineSize;
  color?: MantineColor;
  onChange: (value: string) => void;
}) {
  return (
    <SegmentedControl
      value={value}
      onChange={onChange}
      data={data.map((item) => ({
        value: item.value,
        label: (
          <Tooltip label={item.label} position='top-end'>
            <ActionIcon
              variant='transparent'
              color={color}
              size={size}
              aria-label={`segmented-icon-control-${item.value}`}
              onClick={() => onChange(item.value)}
            >
              {item.icon}
            </ActionIcon>
          </Tooltip>
        )
      }))}
    />
  );
}
