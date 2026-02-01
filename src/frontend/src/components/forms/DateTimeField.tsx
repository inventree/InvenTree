import type { ApiFormFieldType } from '@lib/types/Forms';
import { t } from '@lingui/core/macro';
import { DateTimePicker } from '@mantine/dates';
import dayjs from 'dayjs';
import customParseFormat from 'dayjs/plugin/customParseFormat';
import { useCallback, useId, useMemo } from 'react';
import type { FieldValues, UseControllerReturn } from 'react-hook-form';

dayjs.extend(customParseFormat);

export default function DateTimeField({
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

  const valueFormat = 'YYYY-MM-DD HH:mm:ss';

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
    [field.onChange, definition, valueFormat]
  );

  const dateTimeValue: Date | null = useMemo(() => {
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
    <DateTimePicker
      id={fieldId}
      aria-label={`date-time-field-${field.name}`}
      radius='sm'
      ref={field.ref}
      label={definition.label}
      description={definition.description}
      placeholder={definition.placeholder ?? t`Select date and time`}
      clearable={!definition.required}
      error={definition.error ?? error?.message}
      value={dateTimeValue}
      onChange={onChange}
      valueFormat={valueFormat}
      leftSection={definition.icon}
      highlightToday
      withSeconds
    />
  );
}
