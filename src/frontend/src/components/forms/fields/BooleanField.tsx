import { isTrue } from '@lib/functions/Conversion';
import type { ApiFormFieldType } from '@lib/types/Forms';
import { Switch } from '@mantine/core';
import { useId } from '@mantine/hooks';
import { memo, useCallback, useEffect, useMemo } from 'react';
import type { FieldValues, UseControllerReturn } from 'react-hook-form';

function BooleanFieldComponent({
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

  // Set default value if value is undefined or otherwise empty
  useEffect(() => {
    if (value === undefined || value === null || value === '') {
      onChange(definition.default ?? false);
    }
  }, [value, definition]);

  // Coerce the value to a (stringified) boolean value
  const booleanValue: boolean = useMemo(() => {
    return isTrue(value ?? definition.default ?? false);
  }, [value]);

  const handleChange = useCallback(
    (event: any) => onChange(event.currentTarget.checked || false),
    [onChange]
  );

  return (
    <Switch
      {...definition}
      defaultValue={undefined}
      checked={booleanValue}
      id={fieldId}
      aria-label={`boolean-field-${fieldName}`}
      radius='lg'
      size='sm'
      error={definition.error ?? error?.message}
      onChange={handleChange}
    />
  );
}

export const BooleanField = memo(BooleanFieldComponent);
