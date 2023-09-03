import { t } from '@lingui/macro';
import { Input } from '@mantine/core';
import { UseFormReturnType } from '@mantine/form';
import { useDebouncedValue } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import Select, { Options } from 'react-select';
import AsyncSelect, { useAsync } from 'react-select/async';
import internal from 'stream';

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
  definitions,
  limit = 10
}: {
  formProps: ApiFormProps;
  form: UseFormReturnType<Record<string, unknown>>;
  field: ApiFormFieldType;
  definitions: ApiFormFieldType[];
  limit: number;
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

  const [offset, setOffset] = useState<number>(0);

  const [data, setData] = useState<any[]>([]);

  // Search input query
  const [value, setValue] = useState<string>('');
  const [searchText] = useDebouncedValue(value, 250);

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
            offset: offset,
            limit: limit
          }
        })
        .then((response) => {
          console.log(response);

          let values: any[] = [];

          let results = response.data?.results ?? [];

          results.forEach((item: any) => {
            values.push({
              value: item.pk ?? -1,
              label: item.name ?? item.description ?? item.pk ?? 'Unknown'
            });
          });

          setData(values);
          return response;
        })
        .catch((error) => {
          console.error(error);
          setData([]);
          return error;
        });
    }
  });

  // Update form values when the selected value changes
  function onChange(value: any) {
    let pk = value?.value ?? null;
    form.setValues({ [definition.name]: pk });

    // Run custom callback for this field (if provided)
    if (definition.onValueChange) {
      definition.onValueChange(pk);
    }
  }

  return (
    <Input.Wrapper {...definition}>
      <Select
        options={data}
        filterOption={null}
        onInputChange={(value) => setValue(value)}
        onChange={onChange}
        isLoading={
          selectQuery.isFetching ||
          selectQuery.isLoading ||
          selectQuery.isRefetching
        }
        isClearable={!definition.required}
        isDisabled={definition.disabled}
        isSearchable={true}
        loadingMessage={() => t`Loading...`}
        menuPortalTarget={document.body}
        noOptionsMessage={() => t`No results found`}
        menuPosition="fixed"
        styles={{ menuPortal: (base) => ({ ...base, zIndex: 9999 }) }}
      />
    </Input.Wrapper>
  );
}
