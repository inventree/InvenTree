import {
  Alert,
  Checkbox,
  NumberInput,
  Stack,
  Switch,
  TextInput
} from '@mantine/core';
import { DateInput } from '@mantine/dates';
import { UseFormReturnType } from '@mantine/form';
import { IconX } from '@tabler/icons-react';
import { ReactNode } from 'react';
import { useMemo } from 'react';

import { ApiFormProps } from '../ApiForm';
import { RelatedModelField } from './RelatedModelField';

/* Definition of the ApiForm field component.
 * - The 'name' attribute *must* be provided
 * - All other attributes are optional, and may be provided by the API
 * - However, they can be overridden by the user
 *
 * @param name : The name of the field
 * @param label : The label to display for the field
 * @param value : The value of the field
 * @param default : The default value of the field
 * @param icon : An icon to display next to the field
 * @param fieldType : The type of field to render
 * @param api_url : The API endpoint to fetch data from (for related fields)
 * @param read_only : Whether the field is read-only
 * @param model : The model to use for related fields
 * @param filters : Optional API filters to apply to related fields
 * @param required : Whether the field is required
 * @param hidden : Whether the field is hidden
 * @param disabled : Whether the field is disabled
 * @param placeholder : The placeholder text to display
 * @param description : The description to display for the field
 * @param preFieldContent : Content to render before the field
 * @param postFieldContent : Content to render after the field
 * @param onValueChange : Callback function to call when the field value changes
 */
export type ApiFormFieldType = {
  label?: string;
  value?: any;
  default?: any;
  icon?: ReactNode;
  fieldType?: string;
  api_url?: string;
  read_only?: boolean;
  model?: string;
  filters?: any;
  required?: boolean;
  hidden?: boolean;
  disabled?: boolean;
  placeholder?: string;
  description?: string;
  preFieldContent?: JSX.Element | (() => JSX.Element);
  postFieldContent?: JSX.Element | (() => JSX.Element);
  onValueChange?: (value: any) => void;
};

/*
 * Build a complete field definition based on the provided data
 */
export function constructField({
  form,
  fieldName,
  field,
  definitions
}: {
  form: UseFormReturnType<Record<string, unknown>>;
  fieldName: string;
  field: ApiFormFieldType;
  definitions: Record<string, ApiFormFieldType>;
}) {
  let def = definitions[fieldName] || field;

  def = {
    ...def,
    ...field
  };

  def.disabled = def.disabled || def.read_only;

  // Retrieve the latest value from the form
  let value = form.values[fieldName];

  if (value != undefined) {
    def.value = value;
  }

  // Change value to a date object if required
  switch (def.fieldType) {
    case 'date':
      if (def.value) {
        def.value = new Date(def.value);
      }
      break;
    default:
      break;
  }

  return def;
}

/**
 * Render an individual form field
 */
export function ApiFormField({
  formProps,
  form,
  fieldName,
  field,
  error,
  definitions
}: {
  formProps: ApiFormProps;
  form: UseFormReturnType<Record<string, unknown>>;
  fieldName: string;
  field: ApiFormFieldType;
  error: ReactNode;
  definitions: Record<string, ApiFormFieldType>;
}) {
  // Extract field definition from provided data
  // Where user has provided specific data, override the API definition
  const definition: ApiFormFieldType = useMemo(
    () =>
      constructField({
        form: form,
        fieldName: fieldName,
        field: field,
        definitions: definitions
      }),
    [form.values, field, definitions]
  );

  const preFieldElement: JSX.Element | null = useMemo(() => {
    if (field.preFieldContent === undefined) {
      return null;
    } else if (field.preFieldContent instanceof Function) {
      return field.preFieldContent();
    } else {
      return field.preFieldContent;
    }
  }, [field]);

  const postFieldElement: JSX.Element | null = useMemo(() => {
    if (field.postFieldContent === undefined) {
      return null;
    } else if (field.postFieldContent instanceof Function) {
      return field.postFieldContent();
    } else {
      return field.postFieldContent;
    }
  }, [field]);

  // Callback helper when form value changes
  function onChange(value: any) {
    form.setValues({ [fieldName]: value });

    // Run custom callback for this field
    if (definition.onValueChange) {
      definition.onValueChange(value);
    }
  }

  // Construct the individual field
  function buildField() {
    switch (definition.fieldType) {
      case 'related field':
        return (
          <RelatedModelField
            error={error}
            formProps={formProps}
            form={form}
            field={definition}
            fieldName={fieldName}
            definitions={definitions}
          />
        );
      case 'email':
      case 'url':
      case 'string':
        return (
          <TextInput
            {...definition}
            type={definition.fieldType}
            error={error}
            radius="sm"
            onChange={(event) => onChange(event.currentTarget.value)}
            rightSection={
              definition.value && !definition.required ? (
                <IconX size="1rem" color="red" onClick={() => onChange('')} />
              ) : null
            }
          />
        );
      case 'boolean':
        return (
          <Switch
            radius="lg"
            size="sm"
            {...definition}
            checked={definition.value}
            error={error}
            onChange={(event) => onChange(event.currentTarget.checked)}
          />
        );
      case 'date':
        return (
          <DateInput
            radius="sm"
            {...definition}
            error={error}
            clearable={!definition.required}
            onChange={(value) => onChange(value)}
          />
        );
      case 'integer':
      case 'decimal':
      case 'float':
      case 'number':
        return (
          <NumberInput
            radius="sm"
            {...definition}
            error={error}
            onChange={(value: number) => onChange(value)}
          />
        );
      default:
        return (
          <Alert color="red" title="Error">
            Unknown field type ({field.fieldType}) for field '{fieldName}': '
            {definition.fieldType}'
          </Alert>
        );
    }
  }

  return (
    <Stack>
      {preFieldElement}
      {buildField()}
      {postFieldElement}
    </Stack>
  );
}

export type ApiFormFieldSet = Record<string, ApiFormFieldType>;
