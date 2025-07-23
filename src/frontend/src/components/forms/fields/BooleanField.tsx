import { isTrue } from '@lib/functions/Conversion';
import type { ApiFormFieldType } from '@lib/types/Forms';
import { Switch } from '@mantine/core';
import { useId } from '@mantine/hooks';
import { useMemo } from 'react';
import type { FieldValues, UseControllerReturn } from 'react-hook-form';

export function BooleanField({
  controller,
  definition,
  fieldName,
  onChange
}: Readonly<{
  controller: UseControllerReturn<FieldValues, any>;
  definition: ApiFormFieldType;
  fieldName: string;
  onChange: (value: boolean) => void;
}>) {
  const fieldId = useId();

  const {
    field,
    fieldState: { error }
  } = controller;

  const { value } = field;

  // Coerce the value to a (stringified) boolean value
  const booleanValue: boolean = useMemo(() => {
    return isTrue(value);
  }, [value]);

  return (
    <Switch
      {...definition}
      checked={booleanValue}
      id={fieldId}
      aria-label={`boolean-field-${fieldName}`}
      radius='lg'
      size='sm'
      error={definition.error ?? error?.message}
      onChange={(event: any) => onChange(event.currentTarget.checked || false)}
    />
  );
}
