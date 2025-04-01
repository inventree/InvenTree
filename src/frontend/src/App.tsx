import { QueryClient } from '@tanstack/react-query';
import axios from 'axios';

import { useLocalState } from './states/LocalState';

// Global API instance
export const api = axios.create({});

/*
 * Setup default settings for the Axios API instance.
 */
export function setApiDefaults() {
  const { getHost } = useLocalState.getState();

  api.defaults.baseURL = getHost();
  api.defaults.timeout = 5000;

  api.defaults.withCredentials = true;
  api.defaults.withXSRFToken = true;
  api.defaults.xsrfCookieName = 'csrftoken';
  api.defaults.xsrfHeaderName = 'X-CSRFToken';

  axios.defaults.withCredentials = true;
  axios.defaults.withXSRFToken = true;
  axios.defaults.xsrfHeaderName = 'X-CSRFToken';
  axios.defaults.xsrfCookieName = 'csrftoken';
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false
    }
  }
});
