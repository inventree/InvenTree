import { TextInput } from '@mantine/core';
import { useCallback, useEffect, useId, useMemo, useState } from 'react';
import type { FieldValues, UseControllerReturn } from 'react-hook-form';
import AutoFillRightSection from './AutoFillRightSection';

/*
 * Custom implementation of the mantine <TextInput> component,
 * used for rendering text input fields in forms.
 * Uses a debounced value to prevent excessive re-renders.
 */
export default function TextField({
  controller,
  fieldName,
  definition,
  placeholderAutofill,
  onChange,
  onKeyDown
}: Readonly<{
  controller: UseControllerReturn<FieldValues, any>;
  definition: any;
  fieldName: string;
  placeholderAutofill?: boolean;
  onChange: (value: any) => void;
  onKeyDown: (value: any) => void;
}>) {
  const fieldId = useId();
  const {
    field,
    fieldState: { error }
  } = controller;

  const { value } = useMemo(() => field, [field]);

  const [textValue, setTextValue] = useState<string>(value || '');

  const onTextChange = useCallback(
    (value: any) => {
      setTextValue(value);
      onChange(value);
    },
    [onChange]
  );

  useEffect(() => {
    setTextValue(value || '');
  }, [value]);

  return (
    <TextInput
      {...definition}
      ref={field.ref}
      id={fieldId}
      aria-label={`text-field-${field.name}`}
      type={definition.field_type}
      value={textValue || ''}
      error={definition.error ?? error?.message}
      radius='sm'
      onChange={(event) => onTextChange(event.currentTarget.value)}
      onBlur={(event) => {
        if (event.currentTarget.value != textValue) {
          onTextChange(event.currentTarget.value);
        }
      }}
      onKeyDown={(event) => {
        if (event.code === 'Enter') {
          // Bypass debounce on enter key
          onTextChange(event.currentTarget.value);
        }
        onKeyDown(event.code);
      }}
      rightSection={
        placeholderAutofill && (
          <AutoFillRightSection
            value={textValue}
            fieldName={field.name}
            definition={definition}
            onChange={onChange}
          />
        )
      }
    />
  );
}
