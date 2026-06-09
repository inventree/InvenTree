import { useLocalLibState } from '@lib/states/LocalLibState';
import { Kbd, Table } from '@mantine/core';
import { type UseOSReturnValue, useOs } from '@mantine/hooks';
import type { ContextModalProps } from '@mantine/modals';
import { Fragment, useMemo } from 'react';

function modRenderer(value: string, os: UseOSReturnValue) {
  if (os === 'macos') {
    return value.replace('mod', '⌘');
  }
  return value.replace('mod', 'Ctrl');
}

function kbdRenderer(value: string, os: UseOSReturnValue) {
  const parts = value.split('+');
  if (parts.length > 1) {
    return (
      <>
        {parts.map((part, idx) => (
          <Fragment key={idx}>
            <Kbd>{modRenderer(part, os)}</Kbd>
            {idx < parts.length - 1 && ' + '}
          </Fragment>
        ))}
      </>
    );
  }
  return <Kbd>{modRenderer(value, os)}</Kbd>;
}

export function HotkeyModal({
  context,
  id
}: ContextModalProps<{ modalBody: string }>) {
  const os = useOs();

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
  }, []);
  const data = useMemo(() => {
    return {
      head: ['Hotkey', 'Action'],
      body: [...hotkeys.map((item) => [kbdRenderer(item.key, os), item.dec])]
    };
  }, [os, hotkeys]);

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
