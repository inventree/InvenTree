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
}
