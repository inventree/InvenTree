import { Select } from '@mantine/core';
import { UseFormReturnType } from '@mantine/form';
import { useId } from '@mantine/hooks';
import { ReactNode } from 'react';
import { useMemo } from 'react';

import { constructField } from './ApiFormField';
import { ApiFormFieldSet, ApiFormFieldType } from './ApiFormField';

/**
 * Render a 'select' field for selecting from a list of choices
 */
export function ChoiceField({
  error,
  form,
  fieldName,
  field,
  definitions
}: {
  error: ReactNode;
  form: UseFormReturnType<Record<string, unknown>>;
  field: ApiFormFieldType;
  fieldName: string;
  definitions: ApiFormFieldSet;
}) {
  // Extract field definition from provided data
  // Where user has provided specific data, override the API definition
  const definition: ApiFormFieldType = useMemo(() => {
    let def = constructField({
      form: form,
      field: field,
      fieldName: fieldName,
      definitions: definitions
    });

    return def;
  }, [fieldName, field, definitions]);

  const fieldId = useId(fieldName);

  const value: any = useMemo(() => form.values[fieldName], [form.values]);

  // Build a set of choices for the field
  // TODO: In future, allow this to be created dynamically?
  const choices: any[] = useMemo(() => {
    let choices = definition.choices ?? [];

    // TODO: Allow provision of custom render function also

    return choices.map((choice) => {
      return {
        value: choice.value,
        label: choice.display_name
      };
    });
  }, [definition]);

  // Callback when an option is selected
  function onChange(value: any) {
    form.setFieldValue(fieldName, value);

    if (definition.onValueChange) {
      definition.onValueChange({
        name: fieldName,
        value: value,
        field: definition,
        form: form
      });
    }
  }

  return (
    <Select
      id={fieldId}
      radius="sm"
      {...definition}
      data={choices}
      value={value}
      onChange={(value) => onChange(value)}
      withinPortal={true}
    />
  );
}
