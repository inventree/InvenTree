import type { ApiFormFieldType } from '@lib/types/Forms';
import { JsonInput } from '@mantine/core';
import { useId } from '@mantine/hooks';
import { memo, useCallback, useMemo } from 'react';
import type { FieldValues, UseControllerReturn } from 'react-hook-form';

function JsonFieldComponent({
  controller,
  definition,
  fieldName,
  onChange
}: Readonly<{
  controller: UseControllerReturn<FieldValues, any>;
  definition: ApiFormFieldType;
  fieldName: string;
  onChange: (value: any) => void;
}>) {
  const fieldId = useId();

  const {
    field,
    fieldState: { error }
  } = controller;
  const { value } = field;

  const formattedValue = useMemo(() => {
    if (value === undefined || value === null) {
      return '';
    }

    if (typeof value === 'string') {
      return value;
    }

    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2);
    }

    return String(value);
  }, [value]);

  const handleChange = useCallback(
    (nextValue: string) => {
      if (nextValue.trim() === '') {
        onChange(undefined);
        return;
      }

      try {
        onChange(JSON.parse(nextValue));
      } catch {
        onChange(nextValue);
      }
    },
    [onChange]
  );

  console.log('error', error, 'definition.error', definition.error);

  return (
    <JsonInput
      label={definition.label}
      description={definition.description}
      placeholder={definition.placeholder}
      defaultValue={undefined}
      value={formattedValue}
      id={fieldId}
      aria-label={`json-field-${fieldName}`}
      error={definition.error ?? error?.message}
      onChange={handleChange}
    />
  );
}

export const JsonField = memo(JsonFieldComponent);
