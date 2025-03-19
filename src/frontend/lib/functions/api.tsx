import type { ApiEndpoints, PathParams } from '@lib/core';

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
