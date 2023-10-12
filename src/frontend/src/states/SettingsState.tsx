/**
 * State management for remote (server side) settings
 */
import { create } from 'zustand';

import { api } from '../App';
import { ApiPaths, apiUrl } from './ApiState';
import { Setting } from './states';

interface SettingsStateProps {
  settings: Setting[];
  fetchSettings: () => void;
}

/**
 * State management for global (server side) settings
 */
export const useGlobalSettingsState = create<SettingsStateProps>(
  (set, get) => ({
    settings: [],
    fetchSettings: async () => {
      await api
        .get(apiUrl(ApiPaths.settings_global_list))
        .then((response) => {
          set({ settings: response.data });
        })
        .catch((error) => {
          console.error('Error fetching global settings:', error);
        });
    }
  })
);

/**
 * State management for user (server side) settings
 */
export const useUserSettingsState = create<SettingsStateProps>((set, get) => ({
  settings: [],
  fetchSettings: async () => {
    await api
      .get(apiUrl(ApiPaths.settings_user_list))
      .then((response) => {
        set({ settings: response.data });
      })
      .catch((error) => {
        console.error('Error fetching user settings:', error);
      });
  }
}));
