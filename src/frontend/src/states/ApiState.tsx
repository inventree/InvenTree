import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { AuthConfig, AuthContext } from '@lib/types/Auth';
import { api } from '../App';
import { emptyServerAPI } from '../defaults/defaults';
import type { ServerAPIProps } from './states';

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
