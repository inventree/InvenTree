import { MantineNumberSize } from '@mantine/core';
import { LoaderType } from '@mantine/styles/lib/theme/types/MantineTheme';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import { Locales } from '../contexts/LanguageContext';
import { HostList } from './states';

interface LocalStateProps {
  autoupdate: boolean;
  toggleAutoupdate: () => void;
  host: string;
  setHost: (newHost: string, newHostKey: string) => void;
  hostKey: string;
  hostList: HostList;
  setHostList: (newHostList: HostList) => void;
  language: Locales;
  setLanguage: (newLanguage: Locales) => void;
  // theme
  primaryColor: string;
  whiteColor: string;
  blackColor: string;
  radius: MantineNumberSize;
  loader: LoaderType;
  lastUsedPanels: Record<string, string>;
  setLastUsedPanel: (panelKey: string) => (value: string) => void;
  tableColumnNames: Record<string, Record<string, string>>;
  getTableColumnNames: (tableKey: string) => Record<string, string>;
  setTableColumnNames: (
    tableKey: string
  ) => (names: Record<string, string>) => void;
}

export const useLocalState = create<LocalStateProps>()(
  persist(
    (set, get) => ({
      autoupdate: false,
      toggleAutoupdate: () =>
        set((state) => ({ autoupdate: !state.autoupdate })),
      host: '',
      setHost: (newHost, newHostKey) =>
        set({ host: newHost, hostKey: newHostKey }),
      hostKey: '',
      hostList: {},
      setHostList: (newHostList) => set({ hostList: newHostList }),
      language: 'en',
      setLanguage: (newLanguage) => set({ language: newLanguage }),
      //theme
      primaryColor: 'indigo',
      whiteColor: '#fff',
      blackColor: '#000',
      radius: 'xs',
      loader: 'oval',
      // panels
      lastUsedPanels: {},
      setLastUsedPanel: (panelKey) => (value) => {
        const currentValue = get().lastUsedPanels[panelKey];
        if (currentValue !== value) {
          set({
            lastUsedPanels: { ...get().lastUsedPanels, [panelKey]: value }
          });
        }
      },
      tableColumnNames: {},
      getTableColumnNames: (tableKey) => {
        return get().tableColumnNames[tableKey] || {};
      },
      setTableColumnNames: (tableKey) => (names) => {
        // Update the table column names for the given table
        set({
          tableColumnNames: {
            ...get().tableColumnNames,
            [tableKey]: names
          }
        });
      }
    }),
    {
      name: 'session-settings'
    }
  )
);
