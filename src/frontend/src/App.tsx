import { QueryClient } from '@tanstack/react-query';
import axios from 'axios';

import { getCsrfCookie } from './functions/auth';
import { useLocalState } from './states/LocalState';
import { useSessionState } from './states/SessionState';

// Global API instance
export const api = axios.create({});

/*
 * Setup default settings for the Axios API instance.
 *
 * This includes:
 * - Base URL
 * - Authorization token (if available)
 * - CSRF token (if available)
 */
export function setApiDefaults() {
  const host = useLocalState.getState().host;
  const token = useSessionState.getState().token;

  api.defaults.baseURL = host;

  if (!!token) {
    api.defaults.headers.common['Authorization'] = `Token ${token}`;
  } else {
    api.defaults.headers.common['Authorization'] = undefined;
  }

  if (!!getCsrfCookie()) {
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
