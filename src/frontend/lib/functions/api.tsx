import type { ApiEndpoints } from '../enums/ApiEndpoints';
import type { ModelType } from '../enums/ModelType';
import { ModelInformationDict } from '../enums/ModelType';
import type { PathParams } from '../types/Api';

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
