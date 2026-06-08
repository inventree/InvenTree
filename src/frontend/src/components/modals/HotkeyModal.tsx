import { useLocalLibState } from '@lib/states/LocalLibState';
import { Table } from '@mantine/core';
import type { ContextModalProps } from '@mantine/modals';
import { useMemo } from 'react';

export function HotkeyModal({
  context,
  id
}: ContextModalProps<{ modalBody: string }>) {
  const hotkeys = useMemo(() => {
    const keys = Object.entries(useLocalLibState.getState().hotkeys).map(
      ([hotkey, description]) => {
        return {
          key: hotkey,
          dec: description
        };
      }
    );
    keys.sort((a, b) => a.key.localeCompare(b.key));
    return keys;
  }, [context]);

  const data = useMemo(() => {
    return {
      head: ['Hotkey', 'Action'],
      body: [...hotkeys.map((item) => [item.key, item.dec])]
    };
  }, [context, hotkeys]);

  return (
    <Table
      striped
      highlightOnHover
      withColumnBorders
      horizontalSpacing='md'
      verticalSpacing='xs'
      data={data}
    />
  );
}
