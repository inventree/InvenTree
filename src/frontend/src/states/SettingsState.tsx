/**
 * State management for remote (server side) settings
 */
import { create, createStore } from 'zustand';

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

/**
 * State management for plugin settings
 */
interface CreatePluginSettingStateProps {
  plugin: string;
}

export const createPluginSettingsState = ({
  plugin
}: CreatePluginSettingStateProps) => {
  const pathParams: PathParams = { plugin };

  return createStore<SettingsStateProps>()((set, get) => ({
    settings: [],
    lookup: {},
    endpoint: ApiPaths.plugin_setting_list,
    pathParams,
    fetchSettings: async () => {
      await api
        .get(apiUrl(ApiPaths.plugin_setting_list, undefined, { plugin }))
        .then((response) => {
          const settings = response.data;
          set({
            settings,
            lookup: generate_lookup(settings)
          });
        })
        .catch((error) => {
          console.error(
            `Error fetching plugin settings for plugin ${plugin}:`,
            error
          );
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
};

/**
 * State management for machine settings
 */
interface CreateMachineSettingStateProps {
  machine: string;
  configType: 'M' | 'D';
}

export const createMachineSettingsState = ({
  machine,
  configType
}: CreateMachineSettingStateProps) => {
  const pathParams: PathParams = { machine, config_type: configType };

  return createStore<SettingsStateProps>()((set, get) => ({
    settings: [],
    lookup: {},
    endpoint: ApiPaths.machine_setting_detail,
    pathParams,
    fetchSettings: async () => {
      await api
        .get(apiUrl(ApiPaths.machine_setting_list, undefined, { machine }))
        .then((response) => {
          const settings = response.data.filter(
            (s: any) => s.config_type === configType
          );
          set({
            settings,
            lookup: generate_lookup(settings)
          });
        })
        .catch((error) => {
          console.error(
            `Error fetching machine settings for machine ${machine} with type ${configType}:`,
            error
          );
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
};

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
