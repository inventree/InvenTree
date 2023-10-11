import { t } from '@lingui/macro';
import {
  Alert,
  FileInput,
  NumberInput,
  Stack,
  Switch,
  TextInput
} from '@mantine/core';
import { DateInput } from '@mantine/dates';
import { UseFormReturnType } from '@mantine/form';
import { useId } from '@mantine/hooks';
import { IconX } from '@tabler/icons-react';
import { ReactNode } from 'react';
import { useMemo } from 'react';

import { ModelType } from '../../render/ModelType';
import { ApiFormProps } from '../ApiForm';
import { ChoiceField } from './ChoiceField';
import { RelatedModelField } from './RelatedModelField';

export type ApiFormData = UseFormReturnType<Record<string, unknown>>;

/**
 * Callback function type when a form field value changes
 */
export type ApiFormChangeCallback = {
  name: string;
  value: any;
  field: ApiFormFieldType;
  form: ApiFormData;
};

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
 * @param field_type : The type of field to render
 * @param api_url : The API endpoint to fetch data from (for related fields)
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
 * @param adjustFilters : Callback function to adjust the filters for a related field before a query is made
 */
export type ApiFormFieldType = {
  label?: string;
  value?: any;
  default?: any;
  icon?: ReactNode;
  field_type?: string;
  api_url?: string;
  model?: ModelType;
  filters?: any;
  required?: boolean;
  choices?: any[];
  hidden?: boolean;
  disabled?: boolean;
  placeholder?: string;
  description?: string;
  preFieldContent?: JSX.Element | (() => JSX.Element);
  postFieldContent?: JSX.Element | (() => JSX.Element);
  onValueChange?: (change: ApiFormChangeCallback) => void;
  adjustFilters?: (filters: any, form: ApiFormData) => any;
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

  // Retrieve the latest value from the form
  let value = form.values[fieldName];

  if (value != undefined) {
    def.value = value;
  }

  // Change value to a date object if required
  switch (def.field_type) {
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
  const fieldId = useId(fieldName);

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
    [fieldName, field, definitions]
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
      definition.onValueChange({
        name: fieldName,
        value: value,
        field: definition,
        form: form
      });
    }
  }

  const value: any = useMemo(() => form.values[fieldName], [form.values]);

  // Coerce the value to a numerical value
  const numericalValue: number | undefined = useMemo(() => {
    switch (definition.field_type) {
      case 'integer':
        return parseInt(value);
      case 'decimal':
      case 'float':
      case 'number':
        return parseFloat(value);
      default:
        return undefined;
    }
  }, [value]);

  // Construct the individual field
  function buildField() {
    switch (definition.field_type) {
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
            id={fieldId}
            type={definition.field_type}
            value={value || ''}
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
            {...definition}
            id={fieldId}
            radius="lg"
            size="sm"
            checked={value ?? false}
            error={error}
            onChange={(event) => onChange(event.currentTarget.checked)}
          />
        );
      case 'date':
        return (
          <DateInput
            {...definition}
            id={fieldId}
            radius="sm"
            type={undefined}
            error={error}
            value={value}
            clearable={!definition.required}
            onChange={(value) => onChange(value)}
            valueFormat="YYYY-MM-DD"
          />
        );
      case 'integer':
      case 'decimal':
      case 'float':
      case 'number':
        return (
          <NumberInput
            {...definition}
            radius="sm"
            id={fieldId}
            value={numericalValue}
            error={error}
            onChange={(value: number) => onChange(value)}
          />
        );
      case 'choice':
        return (
          <ChoiceField
            error={error}
            form={form}
            fieldName={fieldName}
            field={definition}
            definitions={definitions}
          />
        );
      case 'file upload':
        return (
          <FileInput
            {...definition}
            id={fieldId}
            radius="sm"
            value={value}
            error={error}
            onChange={(payload: File | null) => onChange(payload)}
          />
        );
      default:
        return (
          <Alert color="red" title={t`Error`}>
            Invalid field type for field '{fieldName}': '{definition.field_type}
            '
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
