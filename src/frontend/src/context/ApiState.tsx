import { create } from 'zustand';

import { api } from '../App';
import { defaultUser, emptyServerAPI } from '../defaults';
import { ServerAPIProps, UserProps } from './states';

interface ApiStateProps {
  user: UserProps | undefined;
  setUser: (newUser: UserProps) => void;
  server: ServerAPIProps;
  setServer: (newServer: ServerAPIProps) => void;
  fetchApiState: () => void;
}

export const useApiState = create<ApiStateProps>((set, get) => ({
  user: defaultUser,
  setUser: (newUser: UserProps) => set({ user: newUser }),
  server: emptyServerAPI,
  setServer: (newServer: ServerAPIProps) => set({ server: newServer }),
  fetchApiState: async () => {
    // Fetch user data
    await api.get(url(ApiPaths.user_me)).then((response) => {
      const user: UserProps = {
        name: `${response.data.first_name} ${response.data.last_name}`,
        email: response.data.email,
        username: response.data.username
      };
      set({ user: user });
    });
    // Fetch server data
    await api.get('/').then((response) => {
      set({ server: response.data });
    });
  }
}));

export enum ApiPaths {
  user_me = 'api-user-me',
  user_token = 'api-user-token',
  user_check = 'api-user-check',
  user_simple_login = 'api-user-simple-login',
  user_reset = 'api-user-reset',
  user_reset_validate = 'api-user-reset-validate',
  user_reset_set = 'api-user-reset-set'
}

export function url(path: ApiPaths, pk?: any): string {
  switch (path) {
    case ApiPaths.user_me:
      return 'user/me/';
    case ApiPaths.user_token:
      return 'user/token/';
    case ApiPaths.user_check:
      return '/api/check/';
    case ApiPaths.user_simple_login:
      return '/api/email_login/';
    case ApiPaths.user_reset:
      return '/api/password_reset/';
    case ApiPaths.user_reset_validate:
      return '/api/password_reset/validate_token/';
    case ApiPaths.user_reset_set:
      return '/api/password_reset/confirm/';

    default:
      return '';
  }
}
