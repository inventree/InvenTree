import { Select } from '@mantine/core';
import { UseFormReturnType } from '@mantine/form';
import { useId } from '@mantine/hooks';
import { ReactNode } from 'react';
import { useMemo } from 'react';

import { ApiFormFieldType } from './ApiFormField';

/**
 * Render a 'select' field for selecting from a list of choices
 */
export function ChoiceField({
  error,
  form,
  fieldName,
  field,
  onChange
}: {
  error: ReactNode;
  form: UseFormReturnType<Record<string, unknown>>;
  field: ApiFormFieldType;
  fieldName: string;
  onChange: (value: string | null) => void;
}) {
  const fieldId = useId(fieldName);

  const value: any = useMemo(() => form.values[fieldName], [form.values]);

  // Build a set of choices for the field
  const choices: any[] = useMemo(() => {
    let choices = field.choices ?? [];

    // TODO: Allow provision of custom render function also

    return choices.map((choice) => {
      return {
        value: choice.value,
        label: choice.display_name
      };
    });
  }, [field.choices]);

  return (
    <Select
      id={fieldId}
      radius="sm"
      {...field}
      onChange={onChange}
      data={choices}
      value={value}
      withinPortal={true}
    />
  );
}
