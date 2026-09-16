import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useLocalLibState = create<LocalLibStateProps>()(
  persist(
    (set, get) => ({
      detailDrawerStack: 0,
      addDetailDrawer: (value) => {
        set({
          detailDrawerStack:
            value === false ? 0 : get().detailDrawerStack + value
        });
      },
      hotkeys: {},
      addHotkeys: (hotkeys) => {
        const newHotkeys = { ...get().hotkeys };
        for (const [ref, details] of hotkeys) {
          newHotkeys[ref] = details;
        }
        set({ hotkeys: newHotkeys });
      },
      removeHotkeys: (hotkeys) => {
        const newHotkeys = { ...get().hotkeys };
        for (const ref of hotkeys) {
          delete newHotkeys[ref];
        }
        set({ hotkeys: newHotkeys });
      }
    }),

    {
      name: 'session-settings-inventreedb_lib'
    }
  )
);
export interface LocalLibStateProps {
  detailDrawerStack: number;
  addDetailDrawer: (value: number | false) => void;
  hotkeys: Record<string, string>;
  addHotkeys: (hotkeys: [string, string][]) => void;
  removeHotkeys: (hotkeys: string[]) => void;
}
