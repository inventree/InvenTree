import { QueryClient } from '@tanstack/react-query';
import axios from 'axios';

import { useLocalState } from './states/LocalState';
import { useUserState } from './states/UserState';

// Global API instance
export const inventreeApi = axios.create({});

/*
 * Setup default settings for the Axios API instance.
 */
export function setApiDefaults() {
  const { host } = useLocalState.getState();
  const { token } = useUserState.getState();

  inventreeApi.defaults.baseURL = host;
  inventreeApi.defaults.timeout = 2500;

  inventreeApi.defaults.withCredentials = true;
  inventreeApi.defaults.withXSRFToken = true;
  inventreeApi.defaults.xsrfCookieName = 'csrftoken';
  inventreeApi.defaults.xsrfHeaderName = 'X-CSRFToken';

  if (token) {
    inventreeApi.defaults.headers.Authorization = `Token ${token}`;
  } else {
    delete inventreeApi.defaults.headers['Authorization'];
  }
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false
    }
  }
});
