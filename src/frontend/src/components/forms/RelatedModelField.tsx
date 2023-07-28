import { Loader, Select } from '@mantine/core';
import { UseFormReturnType } from '@mantine/form';
import { useDebouncedValue } from '@mantine/hooks';
import { QueryErrorResetBoundary, useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

import { api } from '../../App';
import { ApiFormProps } from './ApiForm';
import { ApiFormFieldType } from './ApiFormField';
import { constructField } from './ApiFormField';

/**
 * Render a 'select' field for searching the database against a particular model type
 */
export function RelatedModelField({
  formProps,
  form,
  field,
  definitions
}: {
  formProps: ApiFormProps;
  form: UseFormReturnType<Record<string, unknown>>;
  field: ApiFormFieldType;
  definitions: ApiFormFieldType[];
}) {
  // Extract field definition from provided data
  // Where user has provided specific data, override the API definition
  const definition: ApiFormFieldType = useMemo(
    () =>
      constructField({
        form: form,
        field: field,
        definitions: definitions
      }),
    [form.values, field, definitions]
  );

  const [data, setData] = useState<any[]>([]);

  const [value, setValue] = useState<string>('');
  const [searchText] = useDebouncedValue(value, 500);

  const selectQuery = useQuery({
    enabled: !definition.disabled && !!definition.api_url && !definition.hidden,
    queryKey: [`related-field-${definition.name}`, searchText],
    queryFn: async () => {
      if (!definition.api_url) {
        return null;
      }

      // TODO: Fix this in the api controller
      let url = definition.api_url;

      if (url.startsWith('/api')) {
        url = url.substring(4);
      }

      api
        .get(url, {
          params: {
            search: searchText,
            offset: 0,
            limit: 25
          }
        })
        .then((response) => {
          console.log(response);

          let values: any[] = [];

          let results = response.data?.results ?? [];

          results.forEach((item: any) => {
            values.push({
              value: item.pk ?? -1,
              label: `Item ${item.pk}`
            });
          });

          setData(values);

          console.log('data:', values);

          return response;
        })
        .catch((error) => {
          console.error(error);
          setData([]);
          return error;
        });
    }
  });

  return (
    <Select
      withinPortal={true}
      searchable={true}
      onSearchChange={(value) => setValue(value)}
      data={data}
      clearable={!definition.required}
      {...definition}
      rightSection={selectQuery.isFetching && <Loader size="sm" />}
    />
  );
}
