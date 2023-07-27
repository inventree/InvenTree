import { Alert, Checkbox, NumberInput, Select, TextInput } from '@mantine/core';
import { DateInput } from '@mantine/dates';
import { UseFormReturnType } from '@mantine/form';
import { useDebouncedValue } from '@mantine/hooks';
import { IconX } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useMemo, useState } from 'react';

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
  errors?: string[];
  error?: any;
};

/*
 * Build a complete field definition based on the provided data
 */
function constructField({
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

  // Format the errors
  if (def.errors?.length == 1) {
    def.error = def.errors[0];
  } else if (def.errors?.length ?? 0 > 1) {
    // TODO: Build a custom error stack?
  } else {
    def.error = null;
  }

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
 * Render a 'select' field for searching the database against a particular model type
 */
function RelatedModelField({
  form,
  field,
  definitions
}: {
  form: UseFormReturnType<Record<string, unknown>>;
  field: ApiFormFieldType;
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

  const [value, setValue] = useState<string>('');
  const [searchText] = useDebouncedValue(value, 500);

  const selectQuery = useQuery({
    enabled: !definition.disabled && !!definition.api_url && !definition.hidden,
    queryKey: [`related-field-${definition.name}`, searchText],
    queryFn: async () => {
      console.log('Searching for', searchText);
    }
  });

  function onSearchChange(value: string) {
    console.log('Search change:', value, definition.api_url, definition.model);
    setValue(value);
  }

  return (
    <Select
      withinPortal={true}
      searchable={true}
      onSearchChange={onSearchChange}
      data={[]}
      clearable={!definition.required}
      {...definition}
    />
  );
}

/**
 * Render an individual form field
 */
export function ApiFormField({
  form,
  field,
  definitions,
  onValueChange
}: {
  form: UseFormReturnType<Record<string, unknown>>;
  field: ApiFormFieldType;
  definitions: ApiFormFieldType[];
  onValueChange: (fieldName: string, value: any) => void;
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

  // Callback helper when form value changes
  function onChange(value: any) {
    // onValueChange(definition.name, value);
    form.setValues({ [definition.name]: value });
  }

  switch (definition.fieldType) {
    case 'related field':
      return (
        <RelatedModelField
          form={form}
          field={definition}
          definitions={definitions}
        />
      );
    case 'url':
      return (
        <TextInput
          {...definition}
          type="url"
          onChange={(event) => onChange(event.currentTarget.value)}
          rightSection={
            definition.value && !definition.required ? (
              <IconX size="1rem" color="red" onClick={() => onChange('')} />
            ) : null
          }
        />
      );
    case 'email':
      return (
        <TextInput
          {...definition}
          type="email"
          onChange={(event) => onChange(event.currentTarget.value)}
          rightSection={
            definition.value && !definition.required ? (
              <IconX size="1rem" color="red" onClick={() => onChange('')} />
            ) : null
          }
        />
      );
    case 'string':
      return (
        <TextInput
          {...definition}
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
          onChange={(event) => onChange(event.currentTarget.checked)}
        />
      );
    case 'date':
      return (
        <DateInput
          radius="sm"
          {...definition}
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
