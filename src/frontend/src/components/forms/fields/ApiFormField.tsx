import { t } from '@lingui/core/macro';
import { Alert, FileInput, Stack } from '@mantine/core';
import { useId } from '@mantine/hooks';
import { useCallback, useEffect, useMemo } from 'react';
import { type Control, type FieldValues, useController } from 'react-hook-form';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { ApiFormFieldSet, ApiFormFieldType } from '@lib/types/Forms';
import { IconFileUpload } from '@tabler/icons-react';
import type { NavigateFunction } from 'react-router-dom';
import DateTimeField from '../DateTimeField';
import { BooleanField } from './BooleanField';
import { ChoiceField } from './ChoiceField';
import DateField from './DateField';
import { DependentField } from './DependentField';
import IconField from './IconField';
import { NestedObjectField } from './NestedObjectField';
import NumberField from './NumberField';
import { RelatedModelField } from './RelatedModelField';
import { TableField } from './TableField';
import TagsField from './TagsField';
import TextField from './TextField';
import { TreeField } from './TreeField';

/**
 * Render an individual form field
 */
export function ApiFormField({
  fieldName,
  definition,
  control,
  hideLabels,
  navigate,
  url,
  setFields,
  onKeyDown
}: Readonly<{
  fieldName: string;
  definition: ApiFormFieldType;
  control: Control<FieldValues, any>;
  hideLabels?: boolean;
  navigate?: NavigateFunction | null;
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
      field.onChange(
        definition.adjustValue
          ? definition.adjustValue(definition.value)
          : definition.value
      );
    }
  }, [definition.value, definition.field_type]);

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
      autoFill: undefined,
      placeholderAutofill: undefined,
      placeholderWarning: undefined,
      placeholderWarningCompare: undefined,
      singleFetchFunction: undefined,
      autoFillFilters: undefined,
      onValueChange: undefined,
      adjustFilters: undefined,
      adjustValue: undefined,
      allow_blank: undefined,
      allow_null: undefined,
      read_only: undefined,
      children: undefined,
      exclude: undefined
    };
  }, [fieldDefinition]);

  // Callback helper when form value changes
  const onChange = useCallback(
    (value: any) => {
      let rtnValue: any = value;
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

  // Construct the individual field
  const fieldInstance = useMemo(() => {
    switch (fieldDefinition.field_type) {
      case 'location':
        return (
          <TreeField
            controller={controller}
            definition={fieldDefinition}
            fieldName={fieldName}
            endpoint={ApiEndpoints.stock_location_tree}
            childIdentifier='sublocations'
            genericPlaceholder={t`Select location`}
            model={ModelType.stocklocation}
            navigate={navigate}
          />
        );
      case 'category':
        return (
          <TreeField
            controller={controller}
            definition={fieldDefinition}
            fieldName={fieldName}
            endpoint={ApiEndpoints.category_tree}
            childIdentifier='subcategories'
            genericPlaceholder={t`Select category`}
            model={ModelType.partcategory}
            navigate={navigate}
          />
        );
      case 'related field':
        // Redirect location or category fields to the appropriate tree field
        if (
          fieldDefinition.api_url === apiUrl(ApiEndpoints.stock_location_list)
        ) {
          return (
            <TreeField
              controller={controller}
              definition={fieldDefinition}
              fieldName={fieldName}
              endpoint={ApiEndpoints.stock_location_tree}
              childIdentifier='sublocations'
              genericPlaceholder={t`Select location`}
              model={ModelType.stocklocation}
              navigate={navigate}
            />
          );
        } else if (
          fieldDefinition.api_url === apiUrl(ApiEndpoints.category_list)
        ) {
          return (
            <TreeField
              controller={controller}
              definition={fieldDefinition}
              fieldName={fieldName}
              endpoint={ApiEndpoints.category_tree}
              childIdentifier='subcategories'
              genericPlaceholder={t`Select category`}
              model={ModelType.partcategory}
              navigate={navigate}
            />
          );
        } else {
          return (
            <RelatedModelField
              definition={fieldDefinition}
              controller={controller}
              fieldName={fieldName}
              navigate={navigate}
            />
          );
        }
      case 'email':
      case 'url':
      case 'string':
        return (
          <TextField
            definition={reducedDefinition}
            placeholderAutofill={fieldDefinition.placeholderAutofill ?? false}
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
          <BooleanField
            controller={controller}
            definition={reducedDefinition}
            fieldName={fieldName}
            onChange={(value: boolean) => {
              onChange(value);
            }}
          />
        );
      case 'date':
        return (
          <DateField controller={controller} definition={fieldDefinition} />
        );
      case 'datetime':
        return (
          <DateTimeField controller={controller} definition={fieldDefinition} />
        );
      case 'integer':
      case 'decimal':
      case 'float':
      case 'number':
        return (
          <NumberField
            controller={controller}
            fieldName={fieldName}
            definition={reducedDefinition}
            placeholderAutofill={fieldDefinition.placeholderAutofill ?? false}
            placeholderWarningCompare={
              fieldDefinition.placeholderWarningCompare ?? undefined
            }
            placeholderWarning={fieldDefinition.placeholderWarning ?? undefined}
            onChange={(value: any) => {
              onChange(value);
            }}
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
            clearable={!definition.required}
            aria-label={`file-field-${fieldName}`}
            placeholder={definition.placeholder ?? t`Select file to upload`}
            leftSection={<IconFileUpload />}
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
      case 'tags':
        return (
          <TagsField controller={controller} definition={fieldDefinition} />
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
    control,
    controller,
    definition,
    field,
    fieldId,
    fieldName,
    fieldDefinition,
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
