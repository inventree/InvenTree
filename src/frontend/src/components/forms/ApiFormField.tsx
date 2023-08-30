import {
  Alert,
  Checkbox,
  NumberInput,
  Select,
  Stack,
  TextInput
} from '@mantine/core';
import { DateInput } from '@mantine/dates';
import { UseFormReturnType } from '@mantine/form';
import { IconX } from '@tabler/icons-react';
import { ReactNode } from 'react';
import { useMemo } from 'react';

import { ApiFormProps } from './ApiForm';
import { RelatedModelField } from './RelatedModelField';

/* Definition of the ApiForm field component.
 * - The 'name' attribute *must* be provided
 * - All other attributes are optional, and may be provided by the API
 * - However, they can be overridden by the user
 */
export type ApiFormFieldType = {
  name: string;
  label?: string;
  value?: any;
  default?: any;
  icon?: ReactNode;
  fieldType?: string;
  api_url?: string;
  read_only?: boolean;
  model?: string;
  required?: boolean;
  hidden?: boolean;
  disabled?: boolean;
  placeholder?: string;
  description?: string;
  preFieldContent?: JSX.Element | (() => JSX.Element);
  postFieldContent?: JSX.Element | (() => JSX.Element);
};

/*
 * Build a complete field definition based on the provided data
 */
export function constructField({
  form,
  field,
  definitions
}: {
  form: UseFormReturnType<Record<string, unknown>>;
  field: ApiFormFieldType;
  definitions: ApiFormFieldType[];
}) {
  let def = definitions.find((def) => def.name == field.name) || field;

  def = {
    ...def,
    ...field
  };

  def.disabled = def.disabled || def.read_only;

  // Retrieve the latest value from the form
  let value = form.values[def.name];

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
  field,
  error,
  definitions
}: {
  formProps: ApiFormProps;
  form: UseFormReturnType<Record<string, unknown>>;
  field: ApiFormFieldType;
  error: ReactNode;
  definitions: ApiFormFieldType[];
}) {
  // Extract field definition from provided data
  // Where user has provided specific data, override the API definition
  const definition: ApiFormFieldType = useMemo(
    () =>
      constructField({
        form: form,
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
    form.setValues({ [definition.name]: value });

    // TODO: Implement custom callback for this field
  }

  // Construct the individual field
  function buildField() {
    switch (definition.fieldType) {
      case 'related field':
        return (
          <RelatedModelField
            formProps={formProps}
            form={form}
            field={definition}
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
          <Checkbox
            radius="sm"
            {...definition}
            icon={undefined}
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
            Unknown field type for field '{definition.name}': '
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
