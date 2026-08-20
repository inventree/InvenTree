import { QueryClient } from '@tanstack/react-query';
import axios from 'axios';

import { ApiEndpoints, apiUrl } from '@lib/index';
import { frontendID, serviceName } from './defaults/defaults';
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
export function setTraceId() {
  // check if we are in a secure context (https) - if not use of crypto is not allowed
  if (!window.isSecureContext) {
    return '';
  }

  const runID = crypto.randomUUID().replace(/-/g, '');
  const traceid = `00-${runID}-${frontendID}-01`;
  api.defaults.headers['traceparent'] = traceid;

  return runID;
}
export function removeTraceId(traceid: string) {
  delete api.defaults.headers['traceparent'];

  api
    .post(apiUrl(ApiEndpoints.system_internal_trace_end), {
      traceid: traceid,
      service: serviceName
    })
    .catch((error) => {
      console.error('Error removing trace ID:', error);
    });
}
