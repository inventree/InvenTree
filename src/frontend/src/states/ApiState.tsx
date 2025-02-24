import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

import { api } from '../App';
import { emptyServerAPI } from '../defaults/defaults';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import type { AuthConfig, AuthContext, ServerAPIProps } from './states';

interface ServerApiStateProps {
  server: ServerAPIProps;
  setServer: (newServer: ServerAPIProps) => void;
  fetchServerApiState: () => void;
  auth_config?: AuthConfig;
  auth_context?: AuthContext;
  setAuthContext: (auth_context: AuthContext) => void;
  sso_enabled: () => boolean;
  registration_enabled: () => boolean;
  sso_registration_enabled: () => boolean;
  password_forgotten_enabled: () => boolean;
}

function get_server_setting(val: any) {
  if (val === null || val === undefined) {
    return false;
  }
  return val;
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
            console.error('ERR: Error fetching server info');
          });

        // Fetch login/SSO behaviour
        await api
          .get(apiUrl(ApiEndpoints.auth_config), {
            headers: { Authorization: '' }
          })
          .then((response) => {
            set({ auth_config: response.data.data });
          })
          .catch(() => {
            console.error('ERR: Error fetching SSO information');
          });
      },
      auth_config: undefined,
      auth_context: undefined,
      setAuthContext(auth_context) {
        set({ auth_context });
      },
      sso_enabled: () => {
        const data = get().auth_config?.socialaccount.providers;
        return !(data === undefined || data.length == 0);
      },
      registration_enabled: () => {
        return get_server_setting(get().server?.settings?.registration_enabled);
      },
      sso_registration_enabled: () => {
        return get_server_setting(get().server?.settings?.sso_registration);
      },
      password_forgotten_enabled: () => {
        return get_server_setting(
          get().server?.settings?.password_forgotten_enabled
        );
      }
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
