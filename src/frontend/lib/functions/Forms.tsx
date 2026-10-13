import type { ApiEndpoints } from '../enums/ApiEndpoints';
import type { PathParams } from '../types/Core';
import type { ApiFormFieldSet, ApiFormFieldType } from '../types/Forms';
import { apiUrl } from './Api';

/**
 * Construct an API url from the provided ApiFormProps object
 */
export function constructFormUrl(
  url: ApiEndpoints | string,
  pk?: string | number,
  pathParams?: PathParams,
  queryParams?: URLSearchParams
): string {
  let formUrl = apiUrl(url, pk, pathParams);

  if (queryParams) {
    formUrl += `?${queryParams.toString()}`;
  }

  return formUrl;
}

export type NestedDict = { [key: string]: string | number | NestedDict };

export function mapFields(
  fields: ApiFormFieldSet,
  fieldFunction: (path: string, value: ApiFormFieldType, key: string) => any,
  _path?: string
): NestedDict {
  const res: NestedDict = {};

  for (const [k, v] of Object.entries(fields)) {
    const path = _path ? `${_path}.${k}` : k;
    let value: any;

    if (v.field_type === 'nested object' && v.children) {
      value = mapFields(v.children, fieldFunction, path);
    } else {
      value = fieldFunction(path, v, k);
    }

    if (value !== undefined) res[k] = value;
  }

  return res;
}
