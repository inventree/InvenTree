import { useLocalLibState } from '@lib/states/LocalLibState';
import { Table } from '@mantine/core';
import type { ContextModalProps } from '@mantine/modals';
import { useMemo } from 'react';

export function HotkeyModal({
  context,
  id
}: ContextModalProps<{ modalBody: string }>) {
  const hotkeys = useMemo(() => {
    const keys = useLocalLibState.getState().hotkeys;
    return Object.entries(keys).map(([hotkey, description]) => {
      return {
        key: hotkey,
        dec: description
      };
    });
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
