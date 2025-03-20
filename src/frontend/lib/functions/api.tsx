import { t } from '@lingui/macro';
import { QueryClient } from '@tanstack/react-query';
import axios, { type AxiosInstance } from 'axios';
import type { ApiEndpoints } from '../enums/ApiEndpoints';
import type { ModelType } from '../enums/ModelType';
import { ModelInformationDict } from '../enums/ModelType';
import type { PathParams } from '../types/Api';

import { useLocalState } from '../states/LocalState';

/**
 * Construct an API URL with an endpoint and (optional) pk value
 */
export function apiUrl(
  endpoint: ApiEndpoints | string,
  pk?: any,
  pathParams?: PathParams
): string {
  const API_PREFIX = '/api/';

  let _url = endpoint;

  // If the URL does not start with a '/', add the API prefix
  if (!_url.startsWith('/')) {
    _url = API_PREFIX + _url;
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

/**
 * Returns the detail view URL for a given model type.
 * This is the URL for viewier the details of a single object in the UI
 */
export function getDetailUrl(
  model: ModelType,
  pk: number | string,
  base_url?: string,
  absolute?: boolean
): string {
  const modelInfo = ModelInformationDict[model];

  if (pk === undefined || pk === null) {
    return '';
  }

  if (!!pk && modelInfo && modelInfo.url_detail) {
    const url = modelInfo.url_detail.replace(':pk', pk.toString());
    const base = base_url;

    if (absolute && base) {
      return `/${base}${url}`;
    } else {
      return url;
    }
  }

  // Fallback to console error
  console.error(`No detail URL found for model ${model} <${pk}>`);
  return '';
}

/**
 * Extract a sensible error message from an API error response
 * @param error The error response from the API
 * @param field The field to extract the error message from (optional)
 * @param defaultMessage A default message to use if no error message is found (optional)
 */
export function extractErrorMessage({
  error,
  field,
  defaultMessage
}: {
  error: any;
  field?: string;
  defaultMessage?: string;
}): string {
  const error_data = error.response?.data ?? null;

  let message = '';

  if (error_data) {
    message = error_data[field ?? 'error'] ?? error_data['non_field_errors'];
  }

  // No message? Look at the response status codes
  if (!message) {
    const status = error.response?.status ?? null;

    if (status) {
      switch (status) {
        case 400:
          message = t`Bad request`;
          break;
        case 401:
          message = t`Unauthorized`;
          break;
        case 403:
          message = t`Forbidden`;
          break;
        case 404:
          message = t`Not found`;
          break;
        case 405:
          message = t`Method not allowed`;
          break;
        case 500:
          message = t`Internal server error`;
          break;
        default:
          break;
      }
    }
  }

  if (!message) {
    message = defaultMessage ?? t`An error occurred`;
  }

  return message;
}

/* Global API instance, used for all API requests.
 * Note: This is not exposed directly to the plugin library,
 * rather it is passed through using the useApi() hook
 */

const api = axios.create({});

export function getApi(): AxiosInstance {
  return api;
}

/*
 * Setup default settings for the Axios API instance.
 */
export function setApiDefaults() {
  const { host } = useLocalState.getState();

  api.defaults.baseURL = host;
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
