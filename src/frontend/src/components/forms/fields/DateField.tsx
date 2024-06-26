import { DateInput } from '@mantine/dates';
import dayjs from 'dayjs';
import customParseFormat from 'dayjs/plugin/customParseFormat';
import { useCallback, useId, useMemo } from 'react';
import { FieldValues, UseControllerReturn } from 'react-hook-form';

import { ApiFormFieldType } from './ApiFormField';

dayjs.extend(customParseFormat);

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

  const valueFormat =
    definition.field_type == 'date' ? 'YYYY-MM-DD' : 'YYYY-MM-DD HH:mm:ss';

  const onChange = useCallback(
    (value: any) => {
      // Convert the returned date object to a string
      if (value) {
        value = value.toString();
        value = dayjs(value).format(valueFormat);
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
      aria-label={`date-field-${field.name}`}
      radius="sm"
      ref={field.ref}
      type={undefined}
      error={error?.message}
      value={dateValue}
      clearable={!definition.required}
      onChange={onChange}
      valueFormat={valueFormat}
      label={definition.label}
      description={definition.description}
      placeholder={definition.placeholder}
      leftSection={definition.icon}
    />
  );
}
