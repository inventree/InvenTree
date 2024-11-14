import { useEffect, useMemo } from 'react';
import { FormProvider, useForm } from 'react-hook-form';

import { ApiFormField, type ApiFormFieldType } from './fields/ApiFormField';

export function StandaloneField({
  fieldDefinition,
  fieldName = 'field',
  defaultValue,
  hideLabels,
  error
}: Readonly<{
  fieldDefinition: ApiFormFieldType;
  fieldName?: string;
  defaultValue?: any;
  hideLabels?: boolean;
  error?: string;
}>) {
  // Field must have a defined name
  const name = useMemo(() => fieldName ?? 'field', [fieldName]);

  const defaultValues = useMemo(() => {
    if (defaultValue)
      return {
        [name]: defaultValue
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
      form.setError(name, { message: error });
    }
  }, [form, error]);

  return (
    <FormProvider {...form}>
      <ApiFormField
        fieldName={name}
        definition={fieldDefinition}
        control={form.control}
        hideLabels={hideLabels}
        setFields={undefined}
      />
    </FormProvider>
  );
}
