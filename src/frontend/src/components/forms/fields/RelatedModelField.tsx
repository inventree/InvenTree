import { t } from '@lingui/macro';
import { Input } from '@mantine/core';
import { UseFormReturnType } from '@mantine/form';
import { useDebouncedValue } from '@mantine/hooks';
import { useId } from '@mantine/hooks';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ReactNode, useEffect, useMemo, useState } from 'react';
import Select from 'react-select';

import { api } from '../../../App';
import { RenderInstance } from '../../render/Instance';
import { ApiFormProps } from '../ApiForm';
import { ApiFormFieldSet, ApiFormFieldType } from './ApiFormField';
import { constructField } from './ApiFormField';

/**
 * Render a 'select' field for searching the database against a particular model type
 */
export function RelatedModelField({
  error,
  formProps,
  form,
  fieldName,
  field,
  definitions,
  limit = 10
}: {
  error: ReactNode;
  formProps: ApiFormProps;
  form: UseFormReturnType<Record<string, unknown>>;
  field: ApiFormFieldType;
  fieldName: string;
  definitions: ApiFormFieldSet;
  limit?: number;
}) {
  const fieldId = useId(fieldName);

  // Extract field definition from provided data
  // Where user has provided specific data, override the API definition
  const definition: ApiFormFieldType = useMemo(
    () =>
      constructField({
        form: form,
        field: field,
        fieldName: fieldName,
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
      let formPk = form.values[fieldName] ?? null;

      // If the value is unchanged, do nothing
      if (formPk == pk) {
        return;
      }

      if (formPk != null) {
        let url = (definition.api_url || '') + formPk + '/';

        // TODO: Fix this!!
        if (url.startsWith('/api')) {
          url = url.substring(4);
        }

        api.get(url).then((response) => {
          let data = response.data;

          if (data && data.pk) {
            let value = {
              value: data.pk,
              data: data
            };

            setData([value]);
            setPk(data.pk);
          }
        });
      } else {
        setPk(null);
      }
    }
  }, [form.values[fieldName]]);

  const [offset, setOffset] = useState<number>(0);

  const [data, setData] = useState<any[]>([]);

  // Search input query
  const [value, setValue] = useState<string>('');
  const [searchText, cancelSearchText] = useDebouncedValue(value, 250);

  const selectQuery = useQuery({
    enabled: !definition.disabled && !!definition.api_url && !definition.hidden,
    queryKey: [`related-field-${fieldName}`, offset, searchText],
    queryFn: async () => {
      if (!definition.api_url) {
        return null;
      }

      // TODO: Fix this in the api controller
      let url = definition.api_url;

      if (url.startsWith('/api')) {
        url = url.substring(4);
      }

      let filters = definition.filters ?? {};

      if (definition.adjustFilters) {
        filters = definition.adjustFilters(filters, form);
      }

      let params = {
        ...filters,
        search: searchText,
        offset: offset,
        limit: limit
      };

      return api
        .get(url, {
          params: params
        })
        .then((response) => {
          let values: any[] = [...data];

          let results = response.data?.results ?? response.data ?? [];

          results.forEach((item: any) => {
            values.push({
              value: item.pk ?? -1,
              data: item
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

  /**
   * Format an option for display in the select field
   */
  function formatOption(option: any) {
    let data = option.data ?? option;

    // TODO: If a custom render function is provided, use that

    return (
      <RenderInstance instance={data} model={definition.model ?? 'undefined'} />
    );
  }

  // Update form values when the selected value changes
  function onChange(value: any) {
    let _pk = value?.value ?? null;
    form.setValues({ [fieldName]: _pk });

    setPk(_pk);

    // Run custom callback for this field (if provided)
    if (definition.onValueChange) {
      definition.onValueChange({
        name: fieldName,
        value: _pk,
        field: definition,
        form: form
      });
    }
  }

  return (
    <Input.Wrapper {...definition} error={error}>
      <Select
        id={fieldId}
        value={pk != null && data.find((item) => item.value == pk)}
        options={data}
        filterOption={null}
        onInputChange={(value: any) => {
          setValue(value);
          setOffset(0);
          setData([]);
        }}
        onChange={onChange}
        onMenuScrollToBottom={() => setOffset(offset + limit)}
        onMenuOpen={() => {
          setValue('');
          setOffset(0);
          selectQuery.refetch();
        }}
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
        styles={{ menuPortal: (base: any) => ({ ...base, zIndex: 9999 }) }}
        formatOptionLabel={(option: any) => formatOption(option)}
      />
    </Input.Wrapper>
  );
}
