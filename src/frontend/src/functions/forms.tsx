import { t } from '@lingui/macro';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';
import { AxiosResponse } from 'axios';

import { api } from '../App';
import { ApiForm, ApiFormProps } from '../components/forms/ApiForm';
import {
  ApiFormFieldSet,
  ApiFormFieldType
} from '../components/forms/fields/ApiFormField';
import { StylishText } from '../components/items/StylishText';
import { ApiPaths } from '../enums/ApiEndpoints';
import { PathParams, apiUrl } from '../states/ApiState';
import { invalidResponse, permissionDenied } from './notifications';
import { generateUniqueId } from './uid';

/**
 * Construct an API url from the provided ApiFormProps object
 */
export function constructFormUrl(
  url: ApiPaths | string,
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
  method?: string
): Record<string, ApiFormFieldType> | null {
  // OPTIONS request *must* return 200 status
  if (response.status !== 200) {
    invalidResponse(response.status);
    return null;
  }

  let actions: any = response.data?.actions ?? null;

  if (!method) {
    notifications.show({
      title: t`Form Error`,
      message: t`Form method not provided`,
      color: 'red'
    });
    return null;
  }

  if (!actions) {
    notifications.show({
      title: t`Form Error`,
      message: t`Response did not contain action data`,
      color: 'red'
    });
    return null;
  }

  method = method.toUpperCase();

  if (!(method in actions)) {
    // Missing method - this means user does not have appropriate permission
    permissionDenied();
    return null;
  }

  const processFields = (fields: any, _path?: string) => {
    const _fields: ApiFormFieldSet = {};

    for (const [fieldName, field] of Object.entries(fields) as any) {
      const path = _path ? `${_path}.${fieldName}` : fieldName;
      _fields[fieldName] = {
        ...field,
        name: path,
        field_type: field.type,
        description: field.help_text,
        value: field.value ?? field.default,
        disabled: field.read_only ?? false
      };

      // Remove the 'read_only' field - plays havoc with react components
      delete _fields[fieldName].read_only;

      if (
        _fields[fieldName].field_type === 'nested object' &&
        _fields[fieldName].children
      ) {
        _fields[fieldName].children = processFields(
          _fields[fieldName].children,
          path
        );
      }
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
    let value;

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
    case 'date':
      // Change value to a date object if required
      if (def.value) {
        def.value = new Date(def.value);
      }
      break;
    case 'nested object':
      def.children = {};
      for (const k of Object.keys(field.children ?? {})) {
        def.children[k] = constructField({
          field: field.children?.[k] ?? {},
          definition: definition?.children?.[k] ?? {}
        });
      }
      break;
    default:
      break;
  }

  // Clear out the 'read_only' attribute
  def.disabled = def.disabled ?? def.read_only ?? false;
  delete def['read_only'];

  return def;
}

export interface OpenApiFormProps extends ApiFormProps {
  title: string;
  cancelText?: string;
  cancelColor?: string;
  onClose?: () => void;
}

/*
 * Construct and open a modal form
 * @param title :
 */
export function openModalApiForm(props: OpenApiFormProps) {
  // method property *must* be supplied
  if (!props.method) {
    notifications.show({
      title: t`Invalid Form`,
      message: t`method parameter not supplied`,
      color: 'red'
    });
    return;
  }

  // Generate a random modal ID for controller
  let modalId: string =
    `modal-${props.title}-${props.url}-${props.method}` + generateUniqueId();

  props.actions = [
    ...(props.actions || []),
    {
      text: props.cancelText ?? t`Cancel`,
      color: props.cancelColor ?? 'blue',
      onClick: () => {
        modals.close(modalId);
      }
    }
  ];

  const oldFormSuccess = props.onFormSuccess;
  props.onFormSuccess = (data) => {
    oldFormSuccess?.(data);
    modals.close(modalId);
  };

  let url = constructFormUrl(props.url, props.pk, props.pathParams);

  // Make OPTIONS request first
  api
    .options(url)
    .then((response) => {
      // Extract available fields from the OPTIONS response (and handle any errors)

      let fields: Record<string, ApiFormFieldType> | null = {};

      if (!props.ignorePermissionCheck) {
        fields = extractAvailableFields(response, props.method);

        if (fields == null) {
          return;
        }
      }

      const _props = { ...props };

      if (_props.fields) {
        for (const [k, v] of Object.entries(_props.fields)) {
          _props.fields[k] = constructField({
            field: v,
            definition: fields?.[k]
          });
        }
      }

      modals.open({
        title: <StylishText size="xl">{props.title}</StylishText>,
        modalId: modalId,
        size: 'xl',
        onClose: () => {
          props.onClose ? props.onClose() : null;
        },
        children: <ApiForm id={modalId} props={props} />
      });
    })
    .catch((error) => {
      console.log('Error:', error);
      if (error.response) {
        invalidResponse(error.response.status);
      } else {
        notifications.show({
          title: t`Form Error`,
          message: error.message,
          color: 'red'
        });
      }
    });
}

/**
 * Opens a modal form to create a new model instance
 */
export function openCreateApiForm(props: OpenApiFormProps) {
  let createProps: OpenApiFormProps = {
    ...props,
    method: 'POST'
  };

  openModalApiForm(createProps);
}

/**
 * Open a modal form to edit a model instance
 */
export function openEditApiForm(props: OpenApiFormProps) {
  let editProps: OpenApiFormProps = {
    ...props,
    fetchInitialData: props.fetchInitialData ?? true,
    method: 'PUT'
  };

  openModalApiForm(editProps);
}

/**
 * Open a modal form to delete a model instancel
 */
export function openDeleteApiForm(props: OpenApiFormProps) {
  let deleteProps: OpenApiFormProps = {
    ...props,
    method: 'DELETE',
    submitText: t`Delete`,
    submitColor: 'red',
    fields: {}
  };

  openModalApiForm(deleteProps);
}
