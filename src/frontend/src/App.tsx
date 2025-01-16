import { QueryClient } from '@tanstack/react-query';
import axios from 'axios';

import { useLocalState } from './states/LocalState';
import { useUserState } from './states/UserState';

// Global API instance
export const api = axios.create({});

/*
 * Setup default settings for the Axios API instance.
 */
export function setApiDefaults() {
  const { host } = useLocalState.getState();
  const { token } = useUserState.getState();

  api.defaults.baseURL = host;
  api.defaults.timeout = 5000;

  api.defaults.withCredentials = true;
  api.defaults.withXSRFToken = true;
  api.defaults.xsrfCookieName = 'csrftoken';
  api.defaults.xsrfHeaderName = 'X-CSRFToken';

  if (token) {
    api.defaults.headers.Authorization = `Token ${token}`;
  } else {
    delete api.defaults.headers['Authorization'];
  }
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false
    }
  }
});
