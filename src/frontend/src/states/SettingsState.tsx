/**
 * State management for remote (server side) settings
 */
import { create } from 'zustand';

import { api } from '../App';
import { ApiPaths } from '../enums/ApiEndpoints';
import { isTrue } from '../functions/conversion';
import { PathParams, apiUrl } from './ApiState';
import { Setting, SettingsLookup } from './states';

export interface SettingsStateProps {
  settings: Setting[];
  lookup: SettingsLookup;
  fetchSettings: () => void;
  endpoint: ApiPaths;
  pathParams?: PathParams;
  getSetting: (key: string, default_value?: string) => string; // Return a raw setting value
  isSet: (key: string, default_value?: boolean) => boolean; // Check a "boolean" setting
}

/**
 * State management for global (server side) settings
 */
export const useGlobalSettingsState = create<SettingsStateProps>(
  (set, get) => ({
    settings: [],
    lookup: {},
    endpoint: ApiPaths.settings_global_list,
    fetchSettings: async () => {
      await api
        .get(apiUrl(ApiPaths.settings_global_list))
        .then((response) => {
          set({
            settings: response.data,
            lookup: generate_lookup(response.data)
          });
        })
        .catch((error) => {
          console.error('Error fetching global settings:', error);
        });
    },
    getSetting: (key: string, default_value?: string) => {
      return get().lookup[key] ?? default_value ?? '';
    },
    isSet: (key: string, default_value?: boolean) => {
      let value = get().lookup[key] ?? default_value ?? 'false';
      return isTrue(value);
    }
  })
);

/**
 * State management for user (server side) settings
 */
export const useUserSettingsState = create<SettingsStateProps>((set, get) => ({
  settings: [],
  lookup: {},
  endpoint: ApiPaths.settings_user_list,
  fetchSettings: async () => {
    await api
      .get(apiUrl(ApiPaths.settings_user_list))
      .then((response) => {
        set({
          settings: response.data,
          lookup: generate_lookup(response.data)
        });
      })
      .catch((error) => {
        console.error('Error fetching user settings:', error);
      });
  },
  getSetting: (key: string, default_value?: string) => {
    return get().lookup[key] ?? default_value ?? '';
  },
  isSet: (key: string, default_value?: boolean) => {
    let value = get().lookup[key] ?? default_value ?? 'false';
    return isTrue(value);
  }
}));

/*
  return a lookup dictionary for the value of the provided Setting list
*/
function generate_lookup(data: Setting[]) {
  let lookup_dir: SettingsLookup = {};
  for (let setting of data) {
    lookup_dir[setting.key] = setting.value;
  }
  return lookup_dir;
}
