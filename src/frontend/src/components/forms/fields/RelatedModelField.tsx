import { t } from '@lingui/macro';
import { Input } from '@mantine/core';
import { UseFormReturnType } from '@mantine/form';
import { useDebouncedValue } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { ReactNode, useEffect, useMemo, useState } from 'react';
import Select, { Options } from 'react-select';
import AsyncSelect, { useAsync } from 'react-select/async';
import internal from 'stream';

import { api } from '../../../App';
import { ApiFormProps } from '../ApiForm';
import { ApiFormFieldType } from './ApiFormField';
import { constructField } from './ApiFormField';

/**
 * Render a 'select' field for searching the database against a particular model type
 */
export function RelatedModelField({
  error,
  formProps,
  form,
  field,
  definitions,
  limit = 10
}: {
  error: ReactNode;
  formProps: ApiFormProps;
  form: UseFormReturnType<Record<string, unknown>>;
  field: ApiFormFieldType;
  definitions: ApiFormFieldType[];
  limit?: number;
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

  // Keep track of the primary key value for this field
  const [pk, setPk] = useState<number | null>(null);

  // If an initial value is provided, load from the API
  useEffect(() => {
    // If a value is provided, load the related object
    if (form.values) {
      let formPk = form.values[field.name];

      if (formPk && formPk != pk) {
        console.log(`Loading related object for ${field.name}... (${formPk})`);

        let url = (definition.api_url || '') + formPk + '/';

        // TODO: Fix this!!
        if (url.startsWith('/api')) {
          url = url.substring(4);
        }

        api.get(url).then((response) => {
          let data = response.data;

          if (data) {
            let value = {
              value: data.pk,
              label: data.name ?? data.description ?? data.pk ?? 'Unknown'
            };

            setData([value]);

            console.log('data:', response.data);

            // form.setValues({ [definition.name]: value });
            setPk(data.pk);
          }
        });
      }
    }
  }, [form]);

  const [offset, setOffset] = useState<number>(0);

  const [data, setData] = useState<any[]>([]);

  // Search input query
  const [value, setValue] = useState<string>('');
  const [searchText, cancelSearchText] = useDebouncedValue(value, 250);

  const queryController = new AbortController();

  const selectQuery = useQuery({
    enabled: !definition.disabled && !!definition.api_url && !definition.hidden,
    queryKey: [`related-field-${definition.name}`, offset, searchText],
    queryFn: async () => {
      if (!definition.api_url) {
        return null;
      }

      // TODO: Fix this in the api controller
      let url = definition.api_url;

      if (url.startsWith('/api')) {
        url = url.substring(4);
      }

      return api
        .get(url, {
          signal: queryController.signal,
          params: {
            ...definition.filters,
            search: searchText,
            offset: offset,
            limit: limit
          }
        })
        .then((response) => {
          let values: any[] = [...data];

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
          setData([]);
          return error;
        });
    }
  });

  // Update form values when the selected value changes
  function onChange(value: any) {
    let _pk = value?.value ?? null;
    form.setValues({ [definition.name]: _pk });

    setPk(_pk);

    // Run custom callback for this field (if provided)
    if (definition.onValueChange) {
      definition.onValueChange(pk);
    }
  }

  return (
    <Input.Wrapper {...definition} error={error}>
      <Select
        value={data.find((item) => item.value == pk)}
        options={data}
        filterOption={null}
        onInputChange={(value) => {
          // cancelSearchText();
          queryController.abort();
          setValue(value);
          setOffset(0);
          setData([]);
        }}
        onChange={onChange}
        onMenuScrollToBottom={() => setOffset(offset + limit)}
        isLoading={
          selectQuery.isFetching ||
          selectQuery.isLoading ||
          selectQuery.isRefetching
        }
        isClearable={!definition.required}
        isDisabled={definition.disabled}
        isSearchable={true}
        placeholder={definition.placeholder || t`Search` + `...`}
        loadingMessage={() => t`Loading` + `...`}
        menuPortalTarget={document.body}
        noOptionsMessage={() => t`No results found`}
        menuPosition="fixed"
        styles={{ menuPortal: (base) => ({ ...base, zIndex: 9999 }) }}
      />
    </Input.Wrapper>
  );
}
