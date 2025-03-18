import type { ModelType } from '@lib/core';
import type { MantineStyleProp } from '@mantine/core';
import type { UseFormReturnType } from '@mantine/form';
import type { ReactNode } from 'react';
import type { FieldValues } from 'react-hook-form';

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
 * @param hidden : Whether the field is hidden
 * @param disabled : Whether the field is disabled
 * @param error : Optional error message to display
 * @param exclude : Whether to exclude the field from the submitted data
 * @param placeholder : The placeholder text to display
 * @param description : The description to display for the field
 * @param preFieldContent : Content to render before the field
 * @param postFieldContent : Content to render after the field
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
  exclude?: boolean;
  read_only?: boolean;
  placeholder?: string;
  description?: string;
  preFieldContent?: JSX.Element;
  postFieldContent?: JSX.Element;
  adjustValue?: (value: any) => any;
  onValueChange?: (value: any, record?: any) => void;
  adjustFilters?: (value: ApiFormAdjustFilterType) => any;
  addRow?: () => any;
  headers?: ApiFormFieldHeader[];
  depends_on?: string[];
};

export type ApiFormFieldSet = Record<string, ApiFormFieldType>;
