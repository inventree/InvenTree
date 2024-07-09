import { useMemo } from 'react';
import { FormProvider, useForm } from 'react-hook-form';

import { ApiFormField, ApiFormFieldType } from './fields/ApiFormField';

export function StandaloneField({
  fieldDefinition,
  defaultValue,
  hideLabels
}: {
  fieldDefinition: ApiFormFieldType;
  defaultValue?: any;
  hideLabels?: boolean;
}) {
  const defaultValues = useMemo(() => {
    if (defaultValue)
      return {
        field: defaultValue
      };
    return {};
  }, [defaultValue]);

  const form = useForm<{}>({
    criteriaMode: 'all',
    defaultValues
  });

  return (
    <FormProvider {...form}>
      <ApiFormField
        fieldName="field"
        definition={fieldDefinition}
        control={form.control}
        hideLabels={hideLabels}
      />
    </FormProvider>
  );
}
