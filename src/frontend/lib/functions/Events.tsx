import { useHotkeys } from '@mantine/hooks';
import type { HotkeyItemOptions } from '@mantine/hooks';
import { useEffect } from 'react';
import { useLocalLibState } from '..';

// Helper function to cancel event propagation
export function cancelEvent(event: any) {
  event?.preventDefault();
  event?.stopPropagation();
  event?.nativeEvent?.stopImmediatePropagation();
}

export type InvenTreeHotkeyItem = [
  string,
  string,
  (event: KeyboardEvent) => void,
  HotkeyItemOptions?
];

export function useInvenTreeHotkeys(
  _keys: InvenTreeHotkeyItem[],
  tagsToIgnore?: string[]
) {
  const keyelems: [string, string][] = _keys.map(([key, description]) => [
    key,
    description
  ]);

  const mappedHotkeys: [
    string,
    (event: KeyboardEvent) => void,
    HotkeyItemOptions?
  ][] = _keys.map(([key, _, handler, options]) => [key, handler, options]);
  // Register the hotkeys using the Mantine hook
  useHotkeys(mappedHotkeys, tagsToIgnore);

  // register to helper state to store hotkeys
  // This allows us to display the hotkeys in the UI
  useEffect(() => {
    useLocalLibState.getState().addHotkeys(keyelems);
    return () =>
      useLocalLibState.getState().removeHotkeys(keyelems.map(([key]) => key));
  }, []);
}
