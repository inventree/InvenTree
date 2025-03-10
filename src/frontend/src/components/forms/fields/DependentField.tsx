import { useEffect, useMemo } from 'react';
import {
  type Control,
  type FieldValues,
  useFormContext
} from 'react-hook-form';

import { useApi } from '../../../contexts/ApiContext';
import {
  constructField,
  extractAvailableFields
} from '../../../functions/forms';
import {
  ApiFormField,
  type ApiFormFieldSet,
  type ApiFormFieldType
} from './ApiFormField';

export function DependentField({
  control,
  fieldName,
  definition,
  url,
  setFields
}: Readonly<{
  control: Control<FieldValues, any>;
  definition: ApiFormFieldType;
  fieldName: string;
  url?: string;
  setFields?: React.Dispatch<React.SetStateAction<ApiFormFieldSet>>;
}>) {
  const api = useApi();
  const { watch, resetField } = useFormContext();

  const mappedFieldNames = useMemo(
    () =>
      (definition.depends_on ?? []).map((f) =>
        [...fieldName.split('.').slice(0, -1), f].join('.')
      ),
    [definition.depends_on]
  );

  useEffect(() => {
    const { unsubscribe } = watch(async (values, { name }) => {
      // subscribe only to the fields that this field depends on
      if (!name || !mappedFieldNames.includes(name)) return;
      if (!url || !setFields) return;

      const res = await api.options(url, {
        data: values // provide the current form state to the API
      });

      const fields: Record<string, ApiFormFieldType> | null =
        extractAvailableFields(res, 'POST');

      // update the fields in the form state with the new fields
      setFields((prevFields) => {
        const newFields: Record<string, ReturnType<typeof constructField>> = {};

        for (const [k, v] of Object.entries(prevFields)) {
          newFields[k] = constructField({
            field: v,
            definition: fields?.[k]
          });
        }

        return newFields;
      });

      // reset the current field and all nested values with undefined
      resetField(fieldName, {
        defaultValue: undefined,
        keepDirty: true,
        keepTouched: true
      });
    });

    return () => unsubscribe();
  }, [mappedFieldNames, url, setFields, resetField, fieldName]);

  if (!definition.child) {
    return null;
  }

  return (
    <ApiFormField
      control={control}
      fieldName={fieldName}
      definition={definition.child}
      url={url}
      setFields={setFields}
    />
  );
}
