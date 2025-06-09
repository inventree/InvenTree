import type { ApiFormFieldType } from '@lib/types/Forms';
import { DateInput } from '@mantine/dates';
import dayjs from 'dayjs';
import customParseFormat from 'dayjs/plugin/customParseFormat';
import { useCallback, useId, useMemo } from 'react';
import type { FieldValues, UseControllerReturn } from 'react-hook-form';

dayjs.extend(customParseFormat);

export default function DateField({
  controller,
  definition
}: Readonly<{
  controller: UseControllerReturn<FieldValues, any>;
  definition: ApiFormFieldType;
}>) {
  const fieldId = useId();

  const {
    field,
    fieldState: { error }
  } = controller;

  const valueFormat = useMemo(() => {
    // Determine the format based on the field type
    return definition.field_type == 'date'
      ? 'YYYY-MM-DD'
      : 'YYYY-MM-DD HH:mm:ss';
  }, [definition.field_type]);

  const onChange = useCallback(
    (value: any) => {
      // Convert the returned date object to a string
      if (value) {
        value = value.toString();
        value = dayjs(value).format(valueFormat);
        value = value.toString().split('T')[0];
      }

      field.onChange(value);
      definition.onValueChange?.(value);
    },
    [field.onChange, definition, valueFormat]
  );

  const dateValue: Date | null = useMemo(() => {
    let dv: Date | null = null;

    if (field.value) {
      dv = dayjs(field.value).toDate();
    }

    // Ensure that the date is valid
    if (dv instanceof Date && !Number.isNaN(dv.getTime())) {
      return dv;
    } else {
      return null;
    }
  }, [field.value]);

  return (
    <DateInput
      id={fieldId}
      aria-label={`date-field-${field.name}`}
      radius='sm'
      ref={field.ref}
      type={undefined}
      error={definition.error ?? error?.message}
      value={dateValue}
      clearable={!definition.required}
      onChange={onChange}
      valueFormat={valueFormat}
      label={definition.label}
      description={definition.description}
      placeholder={definition.placeholder}
      leftSection={definition.icon}
      highlightToday
    />
  );
}
