import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

import { api } from '../App';
import { emptyServerAPI } from '../defaults/defaults';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { useGlobalSettingsState, useUserSettingsState } from './SettingsState';
import { useGlobalStatusState } from './StatusState';
import { useUserState } from './UserState';
import { AuthProps, ServerAPIProps } from './states';

interface ServerApiStateProps {
  server: ServerAPIProps;
  setServer: (newServer: ServerAPIProps) => void;
  fetchServerApiState: () => void;
  auth_settings?: AuthProps;
}

export const useServerApiState = create<ServerApiStateProps>()(
  persist(
    (set, get) => ({
      server: emptyServerAPI,
      setServer: (newServer: ServerAPIProps) => set({ server: newServer }),
      fetchServerApiState: async () => {
        // Fetch server data
        await api
          .get(apiUrl(ApiEndpoints.api_server_info))
          .then((response) => {
            set({ server: response.data });
          })
          .catch(() => {
            console.error('Error fetching server info');
          });

        // Fetch login/SSO behaviour
        await api
          .get(apiUrl(ApiEndpoints.sso_providers), {
            headers: { Authorization: '' }
          })
          .then((response) => {
            set({ auth_settings: response.data });
          })
          .catch(() => {
            console.error('Error fetching SSO information');
          });
      },
      status: undefined
    }),
    {
      name: 'server-api-state',
      storage: createJSONStorage(() => sessionStorage)
    }
  )
);

/**
 * Function to return the API prefix.
 * For now it is fixed, but may be configurable in the future.
 */
export function apiPrefix(): string {
  return '/api/';
}

export type PathParams = Record<string, string | number>;

/**
 * Construct an API URL with an endpoint and (optional) pk value
 */
export function apiUrl(
  endpoint: ApiEndpoints | string,
  pk?: any,
  pathParams?: PathParams
): string {
  let _url = endpoint;

  // If the URL does not start with a '/', add the API prefix
  if (!_url.startsWith('/')) {
    _url = apiPrefix() + _url;
  }

  if (_url && pk) {
    if (_url.indexOf(':id') >= 0) {
      _url = _url.replace(':id', `${pk}`);
    } else {
      _url += `${pk}/`;
    }
  }

  if (_url && pathParams) {
    for (const key in pathParams) {
      _url = _url.replace(`:${key}`, `${pathParams[key]}`);
    }
  }

  return _url;
}
