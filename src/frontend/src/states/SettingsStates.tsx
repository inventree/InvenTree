/**
 * State management for remote (server side) settings
 */
import { create, createStore } from 'zustand';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { isTrue } from '@lib/functions/Conversion';
import type { PathParams } from '@lib/types/Core';
import type {
  Setting,
  SettingsLookup,
  SettingsStateProps
} from '@lib/types/Settings';
import { useEffect } from 'react';
import { api } from '../App';
import { useUserState } from './UserState';

/**
 * State management for global (server side) settings
 */
export const useGlobalSettingsState = create<SettingsStateProps>(
  (set, get) => ({
    settings: [],
    loaded: false,
    isError: false,
    lookup: {},
    endpoint: ApiEndpoints.settings_global_list,
    fetchSettings: async () => {
      let success = true;
      const { isLoggedIn } = useUserState.getState();

      if (!isLoggedIn()) {
        set({
          loaded: false,
          isError: true
        });
        return success;
      }

      await api
        .get(apiUrl(ApiEndpoints.settings_global_list))
        .then((response) => {
          set({
            settings: response.data,
            lookup: generate_lookup(response.data),
            loaded: true,
            isError: false
          });
        })
        .catch((_error) => {
          console.error('ERR: Error fetching global settings');
          success = false;

          set({
            loaded: false,
            isError: true
          });
        });

      return success;
    },
    getSetting: (key: string, default_value?: string) => {
      return get().lookup[key] ?? default_value ?? '';
    },
    isSet: (key: string, default_value?: boolean) => {
      const value = get().lookup[key] ?? default_value ?? 'false';
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
  loaded: false,
  isError: false,
  endpoint: ApiEndpoints.settings_user_list,
  fetchSettings: async () => {
    let success = true;
    const { isLoggedIn } = useUserState.getState();

    if (!isLoggedIn()) {
      set({
        loaded: false
      });
      return success;
    }

    await api
      .get(apiUrl(ApiEndpoints.settings_user_list))
      .then((response) => {
        set({
          settings: response.data,
          lookup: generate_lookup(response.data),
          loaded: true
        });
      })
      .catch((_error) => {
        console.error('ERR: Error fetching user settings');
        success = false;
        set({
          loaded: false
        });
      });

    return success;
  },
  getSetting: (key: string, default_value?: string) => {
    return get().lookup[key] ?? default_value ?? '';
  },
  isSet: (key: string, default_value?: boolean) => {
    const value = get().lookup[key] ?? default_value ?? 'false';
    return isTrue(value);
  }
}));

/**
 * State management for plugin settings
 */
interface CreatePluginSettingStateProps {
  plugin: string;
  endpoint: ApiEndpoints;
}

export const createPluginSettingsState = ({
  plugin,
  endpoint
}: CreatePluginSettingStateProps) => {
  const pathParams: PathParams = { plugin };

  const store = createStore<SettingsStateProps>()((set, get) => ({
    settings: [],
    lookup: {},
    loaded: false,
    isError: false,
    endpoint: ApiEndpoints.plugin_setting_list,
    pathParams,
    fetchSettings: async () => {
      let success = true;

      if (!plugin) {
        set({
          loaded: false,
          isError: true
        });

        return false;
      }

      set({
        loaded: false,
        isError: false
      });

      await api
        .get(apiUrl(endpoint, undefined, { plugin }))
        .then((response) => {
          const settings = response.data;
          set({
            settings,
            lookup: generate_lookup(settings),
            loaded: true,
            isError: false
          });
        })
        .catch((_error) => {
          console.error(`Error fetching plugin settings for plugin ${plugin}`);
          success = false;
          set({
            loaded: false,
            isError: true
          });
        });

      return success;
    },
    getSetting: (key: string, default_value?: string) => {
      return get().lookup[key] ?? default_value ?? '';
    },
    isSet: (key: string, default_value?: boolean) => {
      const value = get().lookup[key] ?? default_value ?? 'false';
      return isTrue(value);
    }
  }));

  useEffect(() => {
    console.log('fetching plugin settings for', plugin);
    store.getState().fetchSettings();
  }, [plugin]);

  return store;
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
    loaded: false,
    isError: false,
    endpoint: ApiEndpoints.machine_setting_detail,
    pathParams,
    fetchSettings: async () => {
      let success = true;

      await api
        .get(apiUrl(ApiEndpoints.machine_setting_list, undefined, { machine }))
        .then((response) => {
          const settings = response.data.filter(
            (s: any) => s.config_type === configType
          );
          set({
            settings,
            lookup: generate_lookup(settings),
            loaded: true,
            isError: false
          });
        })
        .catch((error) => {
          console.error(
            `Error fetching machine settings for machine ${machine} with type ${configType}:`,
            error
          );
          success = false;
          set({
            loaded: false,
            isError: true
          });
        });

      return success;
    },
    getSetting: (key: string, default_value?: string) => {
      return get().lookup[key] ?? default_value ?? '';
    },
    isSet: (key: string, default_value?: boolean) => {
      const value = get().lookup[key] ?? default_value ?? 'false';
      return isTrue(value);
    }
  }));
};

/*
  return a lookup dictionary for the value of the provided Setting list
*/
function generate_lookup(data: Setting[]) {
  const lookup_dir: SettingsLookup = {};
  for (const setting of data) {
    lookup_dir[setting.key] = setting.value;
  }
  return lookup_dir;
}
