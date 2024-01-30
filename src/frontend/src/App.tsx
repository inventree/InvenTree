import { QueryClient } from '@tanstack/react-query';
import axios from 'axios';

import { useLocalState } from './states/LocalState';
import { useSessionState } from './states/SessionState';

// API
export const api = axios.create({});

export function setApiDefaults() {
  const host = useLocalState.getState().host;
  const token = useSessionState.getState().token;

  api.defaults.baseURL = host;

  if (!!token) {
    api.defaults.headers.common['Authorization'] = `Token ${token}`;
  } else {
    api.defaults.headers.common['Authorization'] = undefined;
  }

  // CSRF support (needed for POST, PUT, PATCH, DELETE)
  api.defaults.withCredentials = true;
  api.defaults.xsrfCookieName = 'csrftoken';
  api.defaults.xsrfHeaderName = 'X-CSRFToken';
}
export const queryClient = new QueryClient();
