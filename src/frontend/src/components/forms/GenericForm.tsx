import { Trans, t } from '@lingui/macro';
import { Input, NumberInput, Stack, Text, TextInput } from '@mantine/core';
import { Group } from '@mantine/core';

/**
 * Define a "generic" form field.
 */
export type GenericFormField = {
  name: string;
  label: string;
  value?: any;
  type: string;
  required?: boolean;
  placeholder?: string;
  help_text?: string;
  icon?: string;
  errors?: string[];
};

/**
 * Construct a form input based on a GenericFormField definition object
 * @param field - A GenericFormField object
 */
export function GenericFormInput({ field }: { field: GenericFormField }) {
  switch (field.type) {
    case 'text':
    case 'string':
      return (
        <TextInput
          placeholder={field.placeholder || undefined}
          error={field.errors?.length ?? 0 > 0}
        />
      );
    default:
      return (
        <TextInput
          error
          disabled
          placeholder={`Unknown field type: ${field.type}`}
        />
      );
  }
}

/**
 * Construct a form field input group
 */
export function GenericFormInputGroup({ field }: { field: GenericFormField }) {
  return (
    <Stack>
      <Text>{field.label}</Text>
      <GenericFormInput field={field} />
    </Stack>
  );
}

/**
 *
 * Construct a "generic" form, where the fields are defined by the caller.
 */
export function GenericForm({ fields }: { fields: GenericFormField[] }) {
  return (
    <Group>{fields.map((field) => GenericFormInputGroup({ field }))}</Group>
  );
}
