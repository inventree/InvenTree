import { t } from '@lingui/core/macro';
import { Alert, FileInput, NumberInput, Stack, Switch } from '@mantine/core';
import { useId } from '@mantine/hooks';
import { useCallback, useEffect, useMemo } from 'react';
import { type Control, type FieldValues, useController } from 'react-hook-form';

import { isTrue } from '@lib/functions/Conversion';
import type { ApiFormFieldSet, ApiFormFieldType } from '@lib/types/Forms';
import { ChoiceField } from './ChoiceField';
import DateField from './DateField';
import { DependentField } from './DependentField';
import IconField from './IconField';
import { NestedObjectField } from './NestedObjectField';
import { RelatedModelField } from './RelatedModelField';
import { TableField } from './TableField';
import TextField from './TextField';

/**
 * Render an individual form field
 */
export function ApiFormField({
  fieldName,
  definition,
  control,
  hideLabels,
  url,
  setFields,
  onKeyDown
}: Readonly<{
  fieldName: string;
  definition: ApiFormFieldType;
  control: Control<FieldValues, any>;
  hideLabels?: boolean;
  url?: string;
  setFields?: React.Dispatch<React.SetStateAction<ApiFormFieldSet>>;
  onKeyDown?: (value: any) => void;
}>) {
  const fieldId = useId();
  const controller = useController({
    name: fieldName,
    control
  });
  const {
    field,
    fieldState: { error }
  } = controller;
  const { value, ref } = field;

  useEffect(() => {
    if (
      definition.field_type === 'nested object' ||
      definition.field_type === 'dependent field'
    )
      return;

    // hook up the value state to the input field
    if (definition.value !== undefined) {
      field.onChange(definition.value);
    }
  }, [definition.value]);

  const fieldDefinition: ApiFormFieldType = useMemo(() => {
    return {
      ...definition,
      label: hideLabels ? undefined : definition.label,
      description: hideLabels ? undefined : definition.description
    };
  }, [hideLabels, definition]);

  // pull out onValueChange as this can cause strange errors when passing the
  // definition to the input components via spread syntax
  const reducedDefinition = useMemo(() => {
    return {
      ...fieldDefinition,
      onValueChange: undefined,
      adjustFilters: undefined,
      adjustValue: undefined,
      read_only: undefined,
      children: undefined,
      exclude: undefined
    };
  }, [fieldDefinition]);

  // Callback helper when form value changes
  const onChange = useCallback(
    (value: any) => {
      let rtnValue = value;
      // Allow for custom value adjustments (per field)
      if (definition.adjustValue) {
        rtnValue = definition.adjustValue(value);
      }

      field.onChange(rtnValue);

      // Run custom callback for this field
      definition.onValueChange?.(rtnValue);
    },
    [fieldName, definition]
  );

  // Coerce the value to a numerical value
  const numericalValue: number | null = useMemo(() => {
    let val: number | null = 0;

    if (value == null) {
      return null;
    }

    switch (definition.field_type) {
      case 'integer':
        val = Number.parseInt(value) ?? '';
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

  // Coerce the value to a (stringified) boolean value
  const booleanValue: boolean = useMemo(() => {
    return isTrue(value);
  }, [value]);

  // Construct the individual field
  const fieldInstance = useMemo(() => {
    switch (fieldDefinition.field_type) {
      case 'related field':
        return (
          <RelatedModelField
            controller={controller}
            definition={fieldDefinition}
            fieldName={fieldName}
          />
        );
      case 'email':
      case 'url':
      case 'string':
        return (
          <TextField
            definition={reducedDefinition}
            controller={controller}
            fieldName={fieldName}
            onChange={onChange}
            onKeyDown={(value) => {
              onKeyDown?.(value);
            }}
          />
        );
      case 'password':
        return (
          <TextField
            definition={{ ...reducedDefinition, type: 'password' }}
            controller={controller}
            fieldName={fieldName}
            onChange={onChange}
            onKeyDown={(value) => {
              onKeyDown?.(value);
            }}
          />
        );
      case 'icon':
        return (
          <IconField definition={fieldDefinition} controller={controller} />
        );
      case 'boolean':
        return (
          <Switch
            {...reducedDefinition}
            checked={booleanValue}
            ref={ref}
            id={fieldId}
            aria-label={`boolean-field-${fieldName}`}
            radius='lg'
            size='sm'
            error={definition.error ?? error?.message}
            onChange={(event: any) => onChange(event.currentTarget.checked)}
          />
        );
      case 'date':
      case 'datetime':
        return (
          <DateField controller={controller} definition={fieldDefinition} />
        );
      case 'integer':
      case 'decimal':
      case 'float':
      case 'number':
        return (
          <NumberInput
            {...reducedDefinition}
            radius='sm'
            ref={field.ref}
            id={fieldId}
            aria-label={`number-field-${field.name}`}
            value={numericalValue === null ? '' : numericalValue}
            error={definition.error ?? error?.message}
            decimalScale={definition.field_type == 'integer' ? 0 : 10}
            onChange={(value: number | string | null) => {
              if (value != null && value.toString().trim() === '') {
                onChange(null);
              } else {
                onChange(value);
              }
            }}
            step={1}
          />
        );
      case 'choice':
        return (
          <ChoiceField
            controller={controller}
            fieldName={fieldName}
            definition={fieldDefinition}
          />
        );
      case 'file upload':
        return (
          <FileInput
            {...reducedDefinition}
            aria-label={`file-field-${fieldName}`}
            id={fieldId}
            ref={field.ref}
            radius='sm'
            value={value}
            error={definition.error ?? error?.message}
            onChange={(payload: File | null) => onChange(payload)}
          />
        );
      case 'nested object':
        return (
          <NestedObjectField
            definition={fieldDefinition}
            fieldName={fieldName}
            control={control}
            url={url}
            setFields={setFields}
          />
        );
      case 'dependent field':
        return (
          <DependentField
            definition={fieldDefinition}
            fieldName={fieldName}
            control={control}
            url={url}
            setFields={setFields}
          />
        );
      case 'table':
        return (
          <TableField
            definition={fieldDefinition}
            fieldName={fieldName}
            control={controller}
          />
        );
      default:
        return (
          <Alert color='red' title={t`Error`}>
            Invalid field type for field '{fieldName}': '
            {fieldDefinition.field_type}'
          </Alert>
        );
    }
  }, [
    booleanValue,
    control,
    controller,
    definition,
    field,
    fieldId,
    fieldName,
    fieldDefinition,
    numericalValue,
    onChange,
    onKeyDown,
    reducedDefinition,
    ref,
    setFields,
    value
  ]);

  if (fieldDefinition.hidden) {
    return null;
  }

  return (
    <Stack>
      {definition.preFieldContent}
      {fieldInstance}
      {definition.postFieldContent}
    </Stack>
  );
}
