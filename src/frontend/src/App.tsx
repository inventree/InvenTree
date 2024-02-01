import { QueryClient } from '@tanstack/react-query';
import axios from 'axios';

import { getCsrfCookie } from './functions/auth';
import { useLocalState } from './states/LocalState';
import { useSessionState } from './states/SessionState';

// API
export const api = axios.create({});

export function setApiDefaults() {
  const host = useLocalState.getState().host;
  const token = useSessionState.getState().token;
  const cookie = getCsrfCookie();

  api.defaults.baseURL = host;

  if (!!token) {
    api.defaults.headers.common['Authorization'] = `Token ${token}`;
  } else {
    api.defaults.headers.common['Authorization'] = undefined;
  }

  if (cookie) {
    api.defaults.withCredentials = true;
    api.defaults.xsrfCookieName = 'csrftoken';
    api.defaults.xsrfHeaderName = 'X-CSRFToken';
  } else {
    api.defaults.withCredentials = false;
    api.defaults.xsrfCookieName = undefined;
    api.defaults.xsrfHeaderName = undefined;
  }
}
export const queryClient = new QueryClient();
