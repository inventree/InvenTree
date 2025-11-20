import { NumberInput } from '@mantine/core';
import { useId, useMemo } from 'react';
import type { FieldValues, UseControllerReturn } from 'react-hook-form';
import AutoFillRightSection from './AutoFillRightSection';

/**
 * Custom implementation of the mantine <NumberInput> component,
 * used for rendering numerical input fields in forms.
 */
export default function NumberField({
  controller,
  fieldName,
  definition,
  placeholderAutofill,
  onChange
}: Readonly<{
  controller: UseControllerReturn<FieldValues, any>;
  definition: any;
  fieldName: string;
  placeholderAutofill?: boolean;
  onChange: (value: any) => void;
}>) {
  const fieldId = useId();
  const {
    field,
    fieldState: { error }
  } = controller;

  const { value } = field;

  // Coerce the value to a numerical value
  const numericalValue: number | null = useMemo(() => {
    let val: number | null = 0;

    if (value == null || value == undefined || value === '') {
      return null;
    }

    switch (definition.field_type) {
      case 'integer':
        val = Number.parseInt(value, 10) ?? '';
        break;
      case 'decimal':
      case 'float':
      case 'number':
        val = Number.parseFloat(value) ?? '';
        break;
      default:
        break;
    }

    if (Number.isNaN(val) || !Number.isFinite(val)) {
      val = null;
    }

    return val;
  }, [definition.field_type, value]);

  return (
    <NumberInput
      {...definition}
      radius={'sm'}
      ref={field.ref}
      id={fieldId}
      aria-label={`number-field-${field.name}`}
      error={definition.error ?? error?.message}
      value={numericalValue === null ? '' : numericalValue}
      decimalScale={definition.field_type == 'integer' ? 0 : 10}
      step={1}
      onChange={(value: number | string | null) => {
        if (value != null && value.toString().trim() === '') {
          onChange(null);
        } else {
          onChange(value);
        }
      }}
      rightSection={
        definition.placeholder &&
        placeholderAutofill &&
        numericalValue == null && (
          <AutoFillRightSection
            value={field.value}
            fieldName={field.name}
            definition={definition}
            onChange={onChange}
          />
        )
      }
    />
  );
}
