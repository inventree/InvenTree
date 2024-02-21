import { t } from '@lingui/macro';
import {
  Alert,
  FileInput,
  NumberInput,
  Stack,
  Switch,
  Table,
  TextInput
} from '@mantine/core';
import { UseFormReturnType } from '@mantine/form';
import { useId } from '@mantine/hooks';
import { IconX } from '@tabler/icons-react';
import { ReactNode, useCallback, useEffect } from 'react';
import { useMemo } from 'react';
import { Control, FieldValues, useController } from 'react-hook-form';

import { ModelType } from '../../../enums/ModelType';
import { ChoiceField } from './ChoiceField';
import DateField from './DateField';
import { NestedObjectField } from './NestedObjectField';
import { RelatedModelField } from './RelatedModelField';
import { TableField } from './TableField';

export type ApiFormData = UseFormReturnType<Record<string, unknown>>;

export type ApiFormAdjustFilterType = {
  filters: any;
  data: FieldValues;
};

/** Definition of the ApiForm field component.
 * - The 'name' attribute *must* be provided
 * - All other attributes are optional, and may be provided by the API
 * - However, they can be overridden by the user
 *
 * @param name : The name of the field
 * @param label : The label to display for the field
 * @param value : The value of the field
 * @param default : The default value of the field
 * @param icon : An icon to display next to the field
 * @param field_type : The type of field to render
 * @param api_url : The API endpoint to fetch data from (for related fields)
 * @param model : The model to use for related fields
 * @param filters : Optional API filters to apply to related fields
 * @param required : Whether the field is required
 * @param hidden : Whether the field is hidden
 * @param disabled : Whether the field is disabled
 * @param placeholder : The placeholder text to display
 * @param description : The description to display for the field
 * @param preFieldContent : Content to render before the field
 * @param postFieldContent : Content to render after the field
 * @param onValueChange : Callback function to call when the field value changes
 * @param adjustFilters : Callback function to adjust the filters for a related field before a query is made
 */
export type ApiFormFieldType = {
  label?: string;
  value?: any;
  default?: any;
  icon?: ReactNode;
  field_type?:
    | 'related field'
    | 'email'
    | 'url'
    | 'string'
    | 'boolean'
    | 'date'
    | 'integer'
    | 'decimal'
    | 'float'
    | 'number'
    | 'choice'
    | 'file upload'
    | 'nested object'
    | 'table';
  api_url?: string;
  model?: ModelType;
  modelRenderer?: (instance: any) => ReactNode;
  filters?: any;
  children?: { [key: string]: ApiFormFieldType };
  required?: boolean;
  choices?: any[];
  hidden?: boolean;
  disabled?: boolean;
  read_only?: boolean;
  placeholder?: string;
  description?: string;
  preFieldContent?: JSX.Element;
  postFieldContent?: JSX.Element;
  onValueChange?: (value: any) => void;
  adjustFilters?: (value: ApiFormAdjustFilterType) => any;
  headers?: string[];
};

/**
 * Render an individual form field
 */
export function ApiFormField({
  fieldName,
  definition,
  control
}: {
  fieldName: string;
  definition: ApiFormFieldType;
  control: Control<FieldValues, any>;
}) {
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
    if (definition.field_type === 'nested object') return;

    // hook up the value state to the input field
    if (definition.value !== undefined) {
      field.onChange(definition.value);
    }
  }, [definition.value]);

  // pull out onValueChange as this can cause strange errors when passing the
  // definition to the input components via spread syntax
  const reducedDefinition = useMemo(() => {
    return {
      ...definition,
      onValueChange: undefined,
      adjustFilters: undefined,
      read_only: undefined,
      children: undefined
    };
  }, [definition]);

  // Callback helper when form value changes
  const onChange = useCallback(
    (value: any) => {
      field.onChange(value);

      // Run custom callback for this field
      definition.onValueChange?.(value);
    },
    [fieldName, definition]
  );

  // Coerce the value to a numerical value
  const numericalValue: number | '' = useMemo(() => {
    let val: number | '' = 0;

    switch (definition.field_type) {
      case 'integer':
        val = parseInt(value) ?? '';
        break;
      case 'decimal':
      case 'float':
      case 'number':
        val = parseFloat(value) ?? '';
        break;
      default:
        break;
    }

    if (isNaN(val) || !isFinite(val)) {
      val = '';
    }

    return val;
  }, [value]);

  // Construct the individual field
  function buildField() {
    switch (definition.field_type) {
      case 'related field':
        return (
          <RelatedModelField
            controller={controller}
            definition={definition}
            fieldName={fieldName}
          />
        );
      case 'email':
      case 'url':
      case 'string':
        return (
          <TextInput
            {...reducedDefinition}
            ref={ref}
            id={fieldId}
            type={definition.field_type}
            value={value || ''}
            error={error?.message}
            radius="sm"
            onChange={(event) => onChange(event.currentTarget.value)}
            rightSection={
              value && !definition.required ? (
                <IconX size="1rem" color="red" onClick={() => onChange('')} />
              ) : null
            }
          />
        );
      case 'boolean':
        return (
          <Switch
            {...reducedDefinition}
            ref={ref}
            id={fieldId}
            radius="lg"
            size="sm"
            checked={value ?? false}
            error={error?.message}
            onChange={(event) => onChange(event.currentTarget.checked)}
          />
        );
      case 'date':
        return <DateField controller={controller} definition={definition} />;
      case 'integer':
      case 'decimal':
      case 'float':
      case 'number':
        return (
          <NumberInput
            {...reducedDefinition}
            radius="sm"
            ref={ref}
            id={fieldId}
            value={numericalValue}
            error={error?.message}
            formatter={(value) => {
              let v: any = parseFloat(value);

              if (Number.isNaN(v) || !Number.isFinite(v)) {
                return value;
              }

              return `${1 * v.toFixed()}`;
            }}
            precision={definition.field_type == 'integer' ? 0 : 10}
            onChange={(value: number) => onChange(value)}
          />
        );
      case 'choice':
        return (
          <ChoiceField
            controller={controller}
            fieldName={fieldName}
            definition={definition}
          />
        );
      case 'file upload':
        return (
          <FileInput
            {...reducedDefinition}
            id={fieldId}
            ref={ref}
            radius="sm"
            value={value}
            error={error?.message}
            onChange={(payload: File | null) => onChange(payload)}
          />
        );
      case 'nested object':
        return (
          <NestedObjectField
            definition={definition}
            fieldName={fieldName}
            control={control}
          />
        );
      case 'table':
        return (
          <TableField
            definition={definition}
            fieldName={fieldName}
            control={controller}
          />
        );
      default:
        return (
          <Alert color="red" title={t`Error`}>
            Invalid field type for field '{fieldName}': '{definition.field_type}
            '
          </Alert>
        );
    }
  }

  if (definition.hidden) {
    return null;
  }

  return (
    <Stack>
      {definition.preFieldContent}
      {buildField()}
      {definition.postFieldContent}
    </Stack>
  );
}

export type ApiFormFieldSet = Record<string, ApiFormFieldType>;
