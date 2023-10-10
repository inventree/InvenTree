import { UseQueryResult } from '@tanstack/react-query';
import { createContext, useMemo } from 'react';

import { useInstance } from '../hooks/UseInstance';

export type SettingsContextType = {
  settingsData: any[];
  settingsQuery: null | UseQueryResult<any, unknown>;
};

/**
 * Custom context provider, which allows any components to access various settings,
 * and also reload them as required (thus refreshing the UI)
 *
 * - This is used to provide a list of settings to the SettingsList component
 * - Provided settings may be global, per-user, or per-plugin
 */
export const SettingsContext = createContext<SettingsContextType>({
  settingsData: [],
  settingsQuery: null
});

export function InvenTreeSettingsContext({
  url,
  children
}: {
  url: string;
  children: JSX.Element;
}) {
  // Query hook for loading settings from provided URL
  const { instance: settingsData, instanceQuery: settingsQuery } = useInstance({
    url,
    hasPrimaryKey: false,
    fetchOnMount: true,
    defaultValue: []
  });

  // Memoize the query results to pass down
  const settings: SettingsContextType = useMemo(
    () => ({
      settingsData,
      settingsQuery
    }),
    [settingsData]
  );

  return (
    <SettingsContext.Provider value={settings}>
      {children}
    </SettingsContext.Provider>
  );
}
