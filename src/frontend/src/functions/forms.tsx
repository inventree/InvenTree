import type { AxiosResponse } from 'axios';

import type {
  ApiFormFieldSet,
  ApiFormFieldType
} from '../components/forms/fields/ApiFormField';
import type { ApiEndpoints } from '../enums/ApiEndpoints';
import { type PathParams, apiUrl } from '../states/ApiState';
import { invalidResponse, permissionDenied } from './notifications';

/**
 * Construct an API url from the provided ApiFormProps object
 */
export function constructFormUrl(
  url: ApiEndpoints | string,
  pk?: string | number,
  pathParams?: PathParams
): string {
  return apiUrl(url, pk, pathParams);
}

/**
 * Extract the available fields (for a given method) from the response object
 *
 * @returns - A list of field definitions, or null if there was an error
 */
export function extractAvailableFields(
  response: AxiosResponse,
  method?: string,
  hideErrors?: boolean
): Record<string, ApiFormFieldType> | null {
  // OPTIONS request *must* return 200 status
  if (response.status !== 200) {
    invalidResponse(response.status);
    return null;
  }

  const actions: any = response.data?.actions ?? null;

  if (!method || !actions) {
    return null;
  }

  method = method.toUpperCase();

  // PATCH method is supported, but metadata is provided via PUT
  if (method === 'PATCH') {
    method = 'PUT';
  }

  if (!(method in actions)) {
    // Missing method - this means user does not have appropriate permission
    if (!hideErrors) {
      permissionDenied();
    }
    return null;
  }

  const processField = (field: any, fieldName: string) => {
    const resField: ApiFormFieldType = {
      ...field,
      name: fieldName,
      field_type: field.type,
      description: field.help_text,
      value: field.value ?? field.default,
      disabled: field.read_only ?? false
    };

    // Remove the 'read_only' field - plays havoc with react components
    delete resField.read_only;

    if (resField.field_type === 'nested object' && resField.children) {
      resField.children = processFields(resField.children, fieldName);
    }

    if (resField.field_type === 'dependent field' && resField.child) {
      resField.child = processField(resField.child, fieldName);

      // copy over the label from the dependent field to the child field
      if (!resField.child.label) {
        resField.child.label = resField.label;
      }
    }

    return resField;
  };

  const processFields = (fields: any, _path?: string) => {
    const _fields: ApiFormFieldSet = {};

    for (const [fieldName, field] of Object.entries(fields) as any) {
      const path = _path ? `${_path}.${fieldName}` : fieldName;
      _fields[fieldName] = processField(field, path);
    }

    return _fields;
  };

  return processFields(actions[method]);
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

/*
 * Build a complete field definition based on the provided data
 */
export function constructField({
  field,
  definition
}: {
  field: ApiFormFieldType;
  definition?: ApiFormFieldType;
}) {
  const def = {
    ...definition,
    ...field
  };

  switch (def.field_type) {
    case 'nested object':
      def.children = {};
      for (const k of Object.keys(field.children ?? {})) {
        def.children[k] = constructField({
          field: field.children?.[k] ?? {},
          definition: definition?.children?.[k] ?? {}
        });
      }
      break;
    case 'dependent field':
      if (!definition?.child) break;

      def.child = constructField({
        // use the raw definition here as field, since a dependent field cannot be influenced by the frontend
        field: definition.child ?? {}
      });
      break;
    default:
      break;
  }

  // Clear out the 'read_only' attribute
  def.disabled = def.disabled ?? def.read_only ?? false;
  delete def['read_only'];

  return def;
}
