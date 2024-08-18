import { useEffect, useMemo } from 'react';
import { FormProvider, useForm } from 'react-hook-form';

import { ApiFormField, ApiFormFieldType } from './fields/ApiFormField';

export function StandaloneField({
  fieldDefinition,
  fieldName = 'field',
  defaultValue,
  hideLabels,
  error
}: {
  fieldDefinition: ApiFormFieldType;
  fieldName?: string;
  defaultValue?: any;
  hideLabels?: boolean;
  error?: string;
}) {
  const defaultValues = useMemo(() => {
    if (defaultValue)
      return {
        field: defaultValue
      };
    return {};
  }, [defaultValue]);

  const form = useForm({
    criteriaMode: 'all',
    defaultValues
  });

  useEffect(() => {
    form.clearErrors();

    if (!!error) {
      form.setError(fieldName ?? 'field', { message: error });
    }
  }, [form, error]);

  return (
    <FormProvider {...form}>
      <ApiFormField
        fieldName={fieldName ?? 'field'}
        definition={fieldDefinition}
        control={form.control}
        hideLabels={hideLabels}
        setFields={undefined}
      />
    </FormProvider>
  );
}
