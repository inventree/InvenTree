import { t } from '@lingui/macro';
import { Input, useMantineTheme } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { useId } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  FieldValues,
  UseControllerReturn,
  useFormContext
} from 'react-hook-form';
import Select from 'react-select';

import { api } from '../../../App';
import { RenderInstance } from '../../render/Instance';
import { ApiFormFieldType } from './ApiFormField';

/**
 * Render a 'select' field for searching the database against a particular model type
 */
export function RelatedModelField({
  controller,
  fieldName,
  definition,
  limit = 10
}: {
  controller: UseControllerReturn<FieldValues, any>;
  definition: ApiFormFieldType;
  fieldName: string;
  limit?: number;
}) {
  const fieldId = useId();
  const {
    field,
    fieldState: { error }
  } = controller;

  const form = useFormContext();

  // Keep track of the primary key value for this field
  const [pk, setPk] = useState<number | null>(null);

  const [offset, setOffset] = useState<number>(0);

  const [data, setData] = useState<any[]>([]);
  const dataRef = useRef<any[]>([]);

  const [isOpen, setIsOpen] = useState<boolean>(false);

  // If an initial value is provided, load from the API
  useEffect(() => {
    // If the value is unchanged, do nothing
    if (field.value === pk) return;

    if (
      field.value !== null &&
      field.value !== undefined &&
      field.value !== ''
    ) {
      const url = `${definition.api_url}${field.value}/`;
      api.get(url).then((response) => {
        const data = response.data;

        if (data && data.pk) {
          const value = {
            value: data.pk,
            data: data
          };

          setData([value]);
          dataRef.current = [value];
          setPk(data.pk);
        }
      });
    } else {
      setPk(null);
    }
  }, [definition.api_url, field.value]);

  // Search input query
  const [value, setValue] = useState<string>('');
  const [searchText, cancelSearchText] = useDebouncedValue(value, 250);

  const [filters, setFilters] = useState<any>({});

  const resetSearch = useCallback(() => {
    setOffset(0);
    setData([]);
    dataRef.current = [];
  }, []);

  // reset current data on search value change
  useEffect(() => {
    resetSearch();
  }, [searchText, filters]);

  const selectQuery = useQuery({
    enabled:
      isOpen &&
      !definition.disabled &&
      !!definition.api_url &&
      !definition.hidden,
    queryKey: [`related-field-${fieldName}`, fieldId, offset, searchText],
    queryFn: async () => {
      if (!definition.api_url) {
        return null;
      }

      let _filters = definition.filters ?? {};

      if (definition.adjustFilters) {
        _filters =
          definition.adjustFilters({
            filters: _filters,
            data: form.getValues()
          }) ?? _filters;
      }

      // If the filters have changed, clear the data
      if (JSON.stringify(_filters) !== JSON.stringify(filters)) {
        resetSearch();
        setFilters(_filters);
      }

      let params = {
        ..._filters,
        search: searchText,
        offset: offset,
        limit: limit
      };

      return api
        .get(definition.api_url, {
          params: params
        })
        .then((response) => {
          // current values need to be accessed via a ref, otherwise "data" has old values here
          // and this results in no overriding the data which means the current value cannot be displayed
          const values: any[] = [...dataRef.current];
          const alreadyPresentPks = values.map((x) => x.value);

          const results = response.data?.results ?? response.data ?? [];
          console.log('ress', results);
          results.forEach((item: any) => {
            // do not push already existing items into the values array
            if (alreadyPresentPks.includes(item.pk)) return;

            values.push({
              value: item.pk ?? -1,
              data: item
            });
          });

          setData(values);
          dataRef.current = values;
          return response;
        })
        .catch((error) => {
          console.log('Hola', error);
          setData([]);
          return error;
        });
    }
  });

  /**
   * Format an option for display in the select field
   */
  const formatOption = useCallback(
    (option: any) => {
      const data = option.data ?? option;

      if (definition.modelRenderer) {
        return <definition.modelRenderer instance={data} />;
      }

      return (
        <RenderInstance instance={data} model={definition.model ?? undefined} />
      );
    },
    [definition.model, definition.modelRenderer]
  );

  // Update form values when the selected value changes
  const onChange = useCallback(
    (value: any) => {
      let _pk = value?.value ?? null;
      field.onChange(_pk);

      setPk(_pk);

      // Run custom callback for this field (if provided)
      definition.onValueChange?.(_pk);
    },
    [field.onChange, definition]
  );

  /* Construct a "cut-down" version of the definition,
   * which does not include any attributes that the lower components do not recognize
   */
  const fieldDefinition = useMemo(() => {
    return {
      ...definition,
      onValueChange: undefined,
      adjustFilters: undefined,
      read_only: undefined
    };
  }, [definition]);

  const currentValue = useMemo(
    () => pk !== null && data.find((item) => item.value === pk),
    [pk, data]
  );

  // Field doesn't follow Mantine theming
  // Define color theme to pass to field based on Mantine theme
  const theme = useMantineTheme();

  const colors = useMemo(() => {
    let colors: any;
    if (theme.colorScheme === 'dark') {
      colors = {
        neutral0: theme.colors[theme.colorScheme][6],
        neutral5: theme.colors[theme.colorScheme][4],
        neutral10: theme.colors[theme.colorScheme][4],
        neutral20: theme.colors[theme.colorScheme][4],
        neutral30: theme.colors[theme.colorScheme][3],
        neutral40: theme.colors[theme.colorScheme][2],
        neutral50: theme.colors[theme.colorScheme][1],
        neutral60: theme.colors[theme.colorScheme][0],
        neutral70: theme.colors[theme.colorScheme][0],
        neutral80: theme.colors[theme.colorScheme][0],
        neutral90: theme.colors[theme.colorScheme][0],
        primary: theme.colors[theme.primaryColor][7],
        primary25: theme.colors[theme.primaryColor][6],
        primary50: theme.colors[theme.primaryColor][5],
        primary75: theme.colors[theme.primaryColor][4]
      };
    } else {
      colors = {
        neutral0: theme.white,
        neutral5: theme.fn.darken(theme.white, 0.05),
        neutral10: theme.fn.darken(theme.white, 0.1),
        neutral20: theme.fn.darken(theme.white, 0.2),
        neutral30: theme.fn.darken(theme.white, 0.3),
        neutral40: theme.fn.darken(theme.white, 0.4),
        neutral50: theme.fn.darken(theme.white, 0.5),
        neutral60: theme.fn.darken(theme.white, 0.6),
        neutral70: theme.fn.darken(theme.white, 0.7),
        neutral80: theme.fn.darken(theme.white, 0.8),
        neutral90: theme.fn.darken(theme.white, 0.9),
        primary: theme.colors[theme.primaryColor][7],
        primary25: theme.colors[theme.primaryColor][4],
        primary50: theme.colors[theme.primaryColor][5],
        primary75: theme.colors[theme.primaryColor][6]
      };
    }
    return colors;
  }, [theme]);

  return (
    <Input.Wrapper
      {...fieldDefinition}
      error={error?.message}
      styles={{ description: { paddingBottom: '5px' } }}
    >
      <Select
        id={fieldId}
        value={currentValue}
        options={data}
        filterOption={null}
        onInputChange={(value: any) => {
          setValue(value);
          resetSearch();
        }}
        onChange={onChange}
        onMenuScrollToBottom={() => setOffset(offset + limit)}
        onMenuOpen={() => {
          setIsOpen(true);
          setValue('');
          resetSearch();
          selectQuery.refetch();
        }}
        onMenuClose={() => {
          setIsOpen(false);
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
        theme={(theme) => {
          return {
            ...theme,
            colors: {
              ...theme.colors,
              ...colors
            }
          };
        }}
      />
    </Input.Wrapper>
  );
}
