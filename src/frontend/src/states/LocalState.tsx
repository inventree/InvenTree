import type { DataTableSortStatus } from 'mantine-datatable';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import { api } from '../App';
import type { UiSizeType } from '../defaults/formatters';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from './ApiState';
import { useUserState } from './UserState';
import type { HostList } from './states';

interface Theme {
  primaryColor: string;
  whiteColor: string;
  blackColor: string;
  radius: UiSizeType;
  loader: string;
}

interface LocalStateProps {
  autoupdate: boolean;
  toggleAutoupdate: () => void;
  host: string;
  setHost: (newHost: string, newHostKey: string) => void;
  hostKey: string;
  hostList: HostList;
  setHostList: (newHostList: HostList) => void;
  language: string;
  setLanguage: (newLanguage: string, noPatch?: boolean) => void;
  // theme
  usertheme: Theme;
  setTheme: (
    newValues: {
      key: keyof Theme;
      value: string;
    }[],
    noPatch?: boolean
  ) => void;
  // panels
  lastUsedPanels: Record<string, string>;
  setLastUsedPanel: (panelKey: string) => (value: string) => void;
  tableColumnNames: Record<string, Record<string, string>>;
  getTableColumnNames: (tableKey: string) => Record<string, string>;
  setTableColumnNames: (
    tableKey: string
  ) => (names: Record<string, string>) => void;
  tableSorting: Record<string, any>;
  getTableSorting: (tableKey: string) => DataTableSortStatus;
  setTableSorting: (
    tableKey: string
  ) => (sorting: DataTableSortStatus<any>) => void;
  clearTableColumnNames: () => void;
  detailDrawerStack: number;
  addDetailDrawer: (value: number | false) => void;
  navigationOpen: boolean;
  setNavigationOpen: (value: boolean) => void;
  allowMobile: boolean;
  setAllowMobile: (value: boolean) => void;
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
      setLanguage: (newLanguage, noPatch = false) => {
        set({ language: newLanguage });
        if (!noPatch) patchUser('language', newLanguage);
      },
      //theme
      usertheme: {
        primaryColor: 'indigo',
        whiteColor: '#fff',
        blackColor: '#000',
        radius: 'xs',
        loader: 'oval'
      },
      setTheme: (newValues, noPatch = false) => {
        const newTheme = { ...get().usertheme };
        newValues.forEach((val) => {
          newTheme[val.key] = val.value;
        });
        // console.log('setting theme, changed val',newValues.map(a => a.key).join(','), newTheme);
        set({ usertheme: newTheme });
        if (!noPatch) patchUser('theme', newTheme);
      },
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
      // tables
      tableColumnNames: {},
      getTableColumnNames: (tableKey) => {
        return get().tableColumnNames[tableKey] || null;
      },
      setTableColumnNames: (tableKey) => (names) => {
        // Update the table column names for the given table
        set({
          tableColumnNames: {
            ...get().tableColumnNames,
            [tableKey]: names
          }
        });
      },
      clearTableColumnNames: () => {
        set({ tableColumnNames: {} });
      },
      tableSorting: {},
      getTableSorting: (tableKey) => {
        return get().tableSorting[tableKey] || {};
      },
      setTableSorting: (tableKey) => (sorting) => {
        // Update the table sorting for the given table
        set({
          tableSorting: {
            ...get().tableSorting,
            [tableKey]: sorting
          }
        });
      },
      // detail drawers
      detailDrawerStack: 0,
      addDetailDrawer: (value) => {
        set({
          detailDrawerStack:
            value === false ? 0 : get().detailDrawerStack + value
        });
      },
      // navigation
      navigationOpen: false,
      setNavigationOpen: (value) => {
        set({ navigationOpen: value });
      },
      allowMobile: false,
      setAllowMobile: (value) => {
        set({ allowMobile: value });
      }
    }),
    {
      name: 'session-settings'
    }
  )
);

/*
pushes changes in user profile to backend
*/
function patchUser(key: 'language' | 'theme', val: any) {
  const uid = useUserState.getState().userId();
  if (uid) {
    api.patch(apiUrl(ApiEndpoints.user_profile), { [key]: val });
  } else {
    console.log('user not logged in, not patching');
  }
}
