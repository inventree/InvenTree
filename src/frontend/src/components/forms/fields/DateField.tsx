import { DateInput } from '@mantine/dates';
import { useCallback, useId, useMemo } from 'react';
import { FieldValues, UseControllerReturn } from 'react-hook-form';

import { ApiFormFieldType } from './ApiFormField';

export default function DateField({
  controller,
  definition
}: {
  controller: UseControllerReturn<FieldValues, any>;
  definition: ApiFormFieldType;
}) {
  const fieldId = useId();

  const {
    field,
    fieldState: { error }
  } = controller;

  const onChange = useCallback(
    (value: any) => {
      // Convert the returned date object to a string
      if (value) {
        value = value.toString();
        let date = new Date(value);
        value = date.toISOString().split('T')[0];
      }

      field.onChange(value);
      definition.onValueChange?.(value);
    },
    [field.onChange, definition]
  );

  const dateValue = useMemo(() => {
    if (field.value) {
      return new Date(field.value);
    } else {
      return undefined;
    }
  }, [field.value]);

  return (
    <DateInput
      id={fieldId}
      radius="sm"
      type={undefined}
      error={error?.message}
      value={dateValue}
      clearable={!definition.required}
      onChange={onChange}
      valueFormat="YYYY-MM-DD"
      label={definition.label}
      description={definition.description}
      placeholder={definition.placeholder}
      icon={definition.icon}
    />
  );
}
