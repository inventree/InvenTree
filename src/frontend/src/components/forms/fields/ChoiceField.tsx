import { Select } from '@mantine/core';
import { useId } from '@mantine/hooks';
import { useCallback, useMemo } from 'react';
import type { FieldValues, UseControllerReturn } from 'react-hook-form';

import type { ApiFormFieldType } from './ApiFormField';

/**
 * Render a 'select' field for selecting from a list of choices
 */
export function ChoiceField({
  controller,
  definition,
  fieldName
}: Readonly<{
  controller: UseControllerReturn<FieldValues, any>;
  definition: ApiFormFieldType;
  fieldName: string;
}>) {
  const fieldId = useId();

  const {
    field,
    fieldState: { error }
  } = controller;

  const { value } = field;

  // Build a set of choices for the field
  const choices: any[] = useMemo(() => {
    const choices = definition.choices ?? [];

    // TODO: Allow provision of custom render function also

    return choices.map((choice) => {
      return {
        value: choice.value.toString(),
        label: choice.display_name ?? choice.value
      };
    });
  }, [definition.choices]);

  // Update form values when the selected value changes
  const onChange = useCallback(
    (value: any) => {
      field.onChange(value);

      // Run custom callback for this field (if provided)
      definition.onValueChange?.(value);
    },
    [field.onChange, definition]
  );

  const choiceValue = useMemo(() => {
    if (!value) {
      return '';
    } else {
      return value.toString();
    }
  }, [value]);

  return (
    <Select
      id={fieldId}
      aria-label={`choice-field-${field.name}`}
      error={definition.error ?? error?.message}
      radius='sm'
      {...field}
      onChange={onChange}
      data={choices}
      value={choiceValue}
      label={definition.label}
      description={definition.description}
      placeholder={definition.placeholder}
      required={definition.required}
      disabled={definition.disabled}
      leftSection={definition.icon}
      comboboxProps={{ withinPortal: true }}
      searchable
    />
  );
}
