import type { DefaultMantineColor, MantineStyleProp } from '@mantine/core';
import type { UseFormReturnType } from '@mantine/form';
import type { JSX, ReactNode } from 'react';
import type { FieldValues, UseFormReturn } from 'react-hook-form';
import type { ApiEndpoints } from '../enums/ApiEndpoints';
import type { ModelType } from '../enums/ModelType';
import type { PathParams, UiSizeType } from './Core';
import type { TableState } from './Tables';

export interface ApiFormAction {
  text: string;
  variant?: 'outline';
  color?: DefaultMantineColor;
  onClick: () => void;
}

export type ApiFormData = UseFormReturnType<Record<string, unknown>>;

export type ApiFormAdjustFilterType = {
  filters: any;
  data: FieldValues;
};

export type ApiFormFieldChoice = {
  value: any;
  display_name: string;
};

// Define individual headers in a table field
export type ApiFormFieldHeader = {
  title: string;
  style?: MantineStyleProp;
};

/** Definition of the ApiForm field component.
 * - The 'name' attribute *must* be provided
 * - All other attributes are optional, and may be provided by the API
 * - However, they can be overridden by the user
 *
 * @param name : The name of the field
 * @param label : The label to display for the field
 * @param value : The value of the field
 * @param default : The default value of the field
 * @param icon : An icon to display next to the field
 * @param field_type : The type of field to render
 * @param api_url : The API endpoint to fetch data from (for related fields)
 * @param pk_field : The primary key field for the related field (default = "pk")
 * @param model : The model to use for related fields
 * @param filters : Optional API filters to apply to related fields
 * @param required : Whether the field is required
 * @param allow_null: Whether the field allows null values
 * @param allow_blank: Whether the field allows blank values
 * @param hidden : Whether the field is hidden
 * @param disabled : Whether the field is disabled
 * @param error : Optional error message to display
 * @param exclude : Whether to exclude the field from the submitted data
 * @param placeholder : The placeholder text to display
 * @param placeholderAutofill: Whether to allow auto-filling of the placeholder value
 * @param description : The description to display for the field
 * @param preFieldContent : Content to render before the field
 * @param postFieldContent : Content to render after the field
 * @param leftSection : Content to render in the left section of the field
 * @param rightSection : Content to render in the right section of the field
 * @param autoFill: Whether to automatically fill the field with data from the API
 * @param autoFillFilters: Optional filters to apply when auto-filling the field
 * @param onValueChange : Callback function to call when the field value changes
 * @param adjustFilters : Callback function to adjust the filters for a related field before a query is made
 * @param adjustValue : Callback function to adjust the value of the field before it is sent to the API
 * @param addRow : Callback function to add a new row to a table field
 * @param onKeyDown : Callback function to get which key was pressed in the form to handle submission on enter
 */
export type ApiFormFieldType = {
  label?: string;
  value?: any;
  default?: any;
  icon?: ReactNode;
  field_type?:
    | 'related field'
    | 'email'
    | 'url'
    | 'string'
    | 'password'
    | 'icon'
    | 'boolean'
    | 'date'
    | 'datetime'
    | 'integer'
    | 'decimal'
    | 'float'
    | 'number'
    | 'choice'
    | 'file upload'
    | 'nested object'
    | 'dependent field'
    | 'table';
  api_url?: string;
  pk_field?: string;
  model?: ModelType;
  modelRenderer?: (instance: any) => ReactNode;
  filters?: any;
  child?: ApiFormFieldType;
  children?: { [key: string]: ApiFormFieldType };
  required?: boolean;
  error?: string;
  choices?: ApiFormFieldChoice[];
  hidden?: boolean;
  disabled?: boolean;
  allow_null?: boolean;
  allow_blank?: boolean;
  exclude?: boolean;
  read_only?: boolean;
  placeholder?: string;
  placeholderAutofill?: boolean;
  description?: string;
  preFieldContent?: JSX.Element;
  postFieldContent?: JSX.Element;
  leftSection?: JSX.Element;
  rightSection?: JSX.Element;
  autoFill?: boolean;
  autoFillFilters?: any;
  adjustValue?: (value: any) => any;
  onValueChange?: (value: any, record?: any) => void;
  adjustFilters?: (value: ApiFormAdjustFilterType) => any;
  addRow?: () => any;
  headers?: ApiFormFieldHeader[];
  depends_on?: string[];
};

export type ApiFormFieldSet = Record<string, ApiFormFieldType>;

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
 * @param checkClose: A callback function to check if the form can be closed after submission
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
  onFormSuccess?: (data: any, form: UseFormReturn) => void;
  onFormError?: (response: any, form: UseFormReturn) => void;
  processFormData?: (data: any, form: UseFormReturn) => any;
  checkClose?: (data: any, form: UseFormReturn) => boolean;
  table?: TableState;
  modelType?: ModelType;
  follow?: boolean;
  actions?: ApiFormAction[];
  timeout?: number;
}

/**
 * @param title : The title to display in the modal header
 * @param cancelText : Optional custom text to display on the cancel button (default: Cancel)
 * @param cancelColor : Optional custom color for the cancel button (default: blue)
 * @param onClose : A callback function to call when the modal is closed.
 * @param onOpen : A callback function to call when the modal is opened.
 */
export interface ApiFormModalProps extends ApiFormProps {
  title: string;
  modalId?: string;
  cancelText?: string;
  cancelColor?: string;
  onClose?: () => void;
  onOpen?: () => void;
  closeOnClickOutside?: boolean;
  size?: UiSizeType;
}

export interface BulkEditApiFormModalProps extends ApiFormModalProps {
  items: number[];
}

export type StockOperationProps = {
  items?: any[];
  pk?: number;
  filters?: any;
  model: ModelType.stockitem | 'location' | ModelType.part;
  refresh: () => void;
};
