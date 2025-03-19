import type { ApiEndpoints, ModelType, PathParams } from '@lib/core';
import type { ApiFormFieldSet } from '@lib/forms';
import type { TableState } from '@lib/hooks/UseTable';
import type { DefaultMantineColor } from '@mantine/core';
import type { FieldValues } from 'react-hook-form';

export interface ApiFormAction {
  text: string;
  variant?: 'outline';
  color?: DefaultMantineColor;
  onClick: () => void;
}

/**
 * Properties for the ApiForm component
 * @param url : The API endpoint to fetch the form data from
 * @param pk : Optional primary-key value when editing an existing object
 * @param pk_field : Optional primary-key field name (default: pk)
 * @param pathParams : Optional path params for the url
 * @param method : Optional HTTP method to use when submitting the form (default: GET)
 * @param fields : The fields to render in the form
 * @param submitText : Optional custom text to display on the submit button (default: Submit)4
 * @param submitColor : Optional custom color for the submit button (default: green)
 * @param fetchInitialData : Optional flag to fetch initial data from the server (default: true)
 * @param preFormContent : Optional content to render before the form fields
 * @param postFormContent : Optional content to render after the form fields
 * @param successMessage : Optional message to display on successful form submission
 * @param onFormSuccess : A callback function to call when the form is submitted successfully.
 * @param onFormError : A callback function to call when the form is submitted with errors.
 * @param processFormData : A callback function to process the form data before submission
 * @param modelType : Define a model type for this form
 * @param follow : Boolean, follow the result of the form (if possible)
 * @param table : Table to update on success (if provided)
 */
export interface ApiFormProps {
  url: ApiEndpoints | string;
  pk?: number | string;
  pk_field?: string;
  pathParams?: PathParams;
  queryParams?: URLSearchParams;
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  fields?: ApiFormFieldSet;
  focus?: string;
  initialData?: FieldValues;
  submitText?: string;
  submitColor?: string;
  fetchInitialData?: boolean;
  ignorePermissionCheck?: boolean;
  preFormContent?: JSX.Element;
  preFormWarning?: string;
  preFormSuccess?: string;
  postFormContent?: JSX.Element;
  successMessage?: string | null;
  onFormSuccess?: (data: any) => void;
  onFormError?: (response: any) => void;
  processFormData?: (data: any) => any;
  table?: TableState;
  modelType?: ModelType;
  follow?: boolean;
  actions?: ApiFormAction[];
  timeout?: number;
}
