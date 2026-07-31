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
      },

      // Captured pk order for the list a user last navigated *from*,
      // keyed by API endpoint. Used to power next/prev navigation on
      // detail pages within the same filtered/ordered context.
      listNavContexts: {},
      setListNavContext: (endpoint, pks) => {
        set({
          listNavContexts: {
            ...get().listNavContexts,
            [endpoint]: { pks }
          }
        });
      },
      dropListNavPk: (endpoint, pk) => {
        const existing = get().listNavContexts[endpoint];
        if (!existing) return;
        set({
          listNavContexts: {
            ...get().listNavContexts,
            [endpoint]: { pks: existing.pks.filter((p) => p !== pk) }
          }
        });
      }
    }),

    {
      name: 'session-settings-inventreedb_lib',
      // listNavContexts is short-lived navigation state, not a persisted
      // user preference - exclude it from localStorage persistence so
      // stale pk lists don't survive across sessions.
      partialize: (state) => {
        const { listNavContexts, ...rest } = state;
        return rest;
      }
    }
  )
);

export interface ListNavContext {
  pks: number[];
}

export interface LocalLibStateProps {
  detailDrawerStack: number;
  addDetailDrawer: (value: number | false) => void;
  hotkeys: Record<string, string>;
  addHotkeys: (hotkeys: [string, string][]) => void;
  removeHotkeys: (hotkeys: string[]) => void;

  listNavContexts: Record<string, ListNavContext>;
  setListNavContext: (endpoint: string, pks: number[]) => void;
  dropListNavPk: (endpoint: string, pk: number) => void;
}
