import type { DataTableSortStatus } from 'mantine-datatable';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { UserTheme } from '@lib/types/Core';
import type { HostList } from '@lib/types/Server';
import { api } from '../App';
import { useUserState } from './UserState';

interface LocalStateProps {
  autoupdate: boolean;
  toggleAutoupdate: () => void;
  host: string;
  getHost: () => string;
  setHost: (newHost: string, newHostKey: string) => void;
  hostKey: string;
  hostList: HostList;
  setHostList: (newHostList: HostList) => void;
  language: string;
  setLanguage: (newLanguage: string, noPatch?: boolean) => void;
  userTheme: UserTheme;
  setTheme: (
    newValues: {
      key: keyof UserTheme;
      value: string;
    }[],
    noPatch?: boolean
  ) => void;
  widgets: string[];
  setWidgets: (widgets: string[], noPatch?: boolean) => void;
  layouts: any;
  setLayouts: (layouts: any, noPatch?: boolean) => void;
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
      getHost: () => {
        // Retrieve and validate the API host
        const state = get();

        let host = state.host;

        // If the server provides an override for the host, use that
        if (window.INVENTREE_SETTINGS?.api_host) {
          host = window.INVENTREE_SETTINGS.api_host;
        }

        // If no host is provided, use the first host in the list
        if (!host && Object.keys(state.hostList).length) {
          host = Object.values(state.hostList)[0].host;
        }

        // If no host is provided, fallback to using the current URL (default)
        if (!host) {
          host = window.location.origin;
        }
        return host;
      },
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
      userTheme: {
        primaryColor: 'indigo',
        whiteColor: '#fff',
        blackColor: '#000',
        radius: 'xs',
        loader: 'oval'
      },
      setTheme: (newValues, noPatch = false) => {
        const newTheme = { ...get().userTheme };
        newValues.forEach((val) => {
          newTheme[val.key] = val.value;
        });
        set({ userTheme: newTheme });
        if (!noPatch) patchUser('theme', newTheme);
      },
      widgets: [],
      setWidgets: (newWidgets, noPatch = false) => {
        // check for difference
        const currentWidgets = get().widgets;
        if (JSON.stringify(newWidgets) === JSON.stringify(currentWidgets)) {
          console.log('no change in widgets');
          return;
        }

        console.log('setWidgets', newWidgets, noPatch, currentWidgets);
        set({ widgets: newWidgets });
        if (!noPatch)
          patchUser('widgets', { widgets: newWidgets, layouts: get().layouts });
      },
      layouts: {},
      setLayouts: (newLayouts, noPatch) => {
        // check for difference
        const currentLayouts = get().layouts;
        if (JSON.stringify(newLayouts) === JSON.stringify(currentLayouts)) {
          console.log('no change in layouts');
          return;
        }

        console.log('setLayouts', newLayouts, noPatch, currentLayouts);
        set({ layouts: newLayouts });
        if (!noPatch)
          patchUser('widgets', { widgets: get().widgets, layouts: newLayouts });
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
function patchUser(key: 'language' | 'theme' | 'widgets', val: any) {
  const uid = useUserState.getState().userId();
  if (uid) {
    api.patch(apiUrl(ApiEndpoints.user_profile), { [key]: val });
  } else {
    console.log('user not logged in, not patching');
  }
}
