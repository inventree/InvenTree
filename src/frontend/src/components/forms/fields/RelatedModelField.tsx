import { t } from '@lingui/core/macro';
import {
  Group,
  Input,
  darken,
  useMantineColorScheme,
  useMantineTheme
} from '@mantine/core';
import { useDebouncedValue, useId } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  type FieldValues,
  type UseControllerReturn,
  useFormContext
} from 'react-hook-form';
import Select from 'react-select';

import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ApiFormFieldType } from '@lib/types/Forms';
import { useApi } from '../../../contexts/ApiContext';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../../states/SettingsStates';
import { vars } from '../../../theme';
import { ScanButton } from '../../buttons/ScanButton';
import Expand from '../../items/Expand';
import { RenderInstance } from '../../render/Instance';

/**
 * Render a 'select' field for searching the database against a particular model type
 */
export function RelatedModelField({
  controller,
  fieldName,
  definition,
  limit = 10
}: Readonly<{
  controller: UseControllerReturn<FieldValues, any>;
  definition: ApiFormFieldType;
  fieldName: string;
  limit?: number;
}>) {
  const api = useApi();
  const fieldId = useId();
  const {
    field,
    fieldState: { error }
  } = controller;

  const form = useFormContext();

  // Keep track of the primary key value for this field
  const [pk, setPk] = useState<number | null>(null);

  // Handle condition where the form is rebuilt dynamically
  useEffect(() => {
    const value = field.value || pk;
    if (value && value != form.getValues()[fieldName]) {
      form.setValue(fieldName, value);
    }
  }, [pk, field.value]);

  const [offset, setOffset] = useState<number>(0);

  const [initialData, setInitialData] = useState<{}>({});
  const [data, setData] = useState<any[]>([]);
  const dataRef = useRef<any[]>([]);

  const globalSettings = useGlobalSettingsState();
  const userSettings = useUserSettingsState();

  // Search input query
  const [value, setValue] = useState<string>('');
  const [searchText] = useDebouncedValue(value, 250);

  // Fetch a single field by primary key, using the provided API filters
  const fetchSingleField = useCallback(
    (pk: number) => {
      if (!definition?.api_url) {
        return;
      }

      const params = definition?.filters ?? {};
      const url = `${definition.api_url}${pk}/`;

      api
        .get(url, {
          params: params
        })
        .then((response) => {
          const pk_field = definition.pk_field ?? 'pk';
          if (response.data?.[pk_field]) {
            const value = {
              value: response.data[pk_field],
              data: response.data
            };

            // Run custom callback for this field (if provided)
            if (definition.onValueChange) {
              definition.onValueChange(response.data[pk_field], response.data);
            }

            setInitialData(value);
            dataRef.current = [value];
            setPk(response.data[pk_field]);
          }
        });
    },
    [
      definition.api_url,
      definition.filters,
      definition.onValueChange,
      definition.pk_field,
      setValue,
      setPk
    ]
  );

  // Memoize the model type information for this field
  const modelInfo = useMemo(() => {
    if (!definition.model) {
      return null;
    }
    return ModelInformationDict[definition.model];
  }, [definition.model]);

  // Determine whether a barcode field should be added
  const addBarcodeField: boolean = useMemo(() => {
    if (!modelInfo || !modelInfo.supports_barcode) {
      return false;
    }

    if (!globalSettings.isSet('BARCODE_ENABLE')) {
      return false;
    }

    if (!userSettings.isSet('BARCODE_IN_FORM_FIELDS')) {
      return false;
    }

    return true;
  }, [globalSettings, userSettings, modelInfo]);

  // Callback function to handle barcode scan results
  const onBarcodeScan = useCallback(
    (barcode: string, response: any) => {
      // Fetch model information from the response
      const modelData = response?.[definition.model ?? ''] ?? null;

      if (modelData) {
        const pk_field = definition.pk_field ?? 'pk';
        const pk = modelData[pk_field];

        if (pk) {
          // Perform a full re-fetch of the field data
          // This is necessary as the barcode scan does not provide full data necessarily
          fetchSingleField(pk);
        }
      }
    },
    [definition.model, definition.pk_field, fetchSingleField]
  );

  const [isOpen, setIsOpen] = useState<boolean>(false);

  const [autoFilled, setAutoFilled] = useState<boolean>(false);

  useEffect(() => {
    // Reset auto-fill status when the form is reconstructed
    setAutoFilled(false);
  }, []);

  // Auto-fill the field with data from the API
  useEffect(() => {
    // If there is *no value defined*, and autoFill is enabled, then fetch data from the API
    if (!definition.autoFill || !definition.api_url) {
      return;
    }

    // Return if the autofill has already been performed
    if (autoFilled) {
      return;
    }

    if (field.value != undefined) {
      return;
    }

    setAutoFilled(true);

    // Construct parameters for auto-filling the field
    const params = {
      ...(definition?.filters ?? {}),
      ...(definition?.autoFillFilters ?? {})
    };

    api
      .get(definition.api_url, {
        params: {
          ...params,
          limit: 1,
          offset: 0
        }
      })
      .then((response) => {
        const data: any = response?.data ?? {};

        if (data.count === 1 && data.results?.length === 1) {
          // If there is only a single result, set the field value to that result
          const pk_field = definition.pk_field ?? 'pk';
          if (data.results[0][pk_field]) {
            const value = {
              value: data.results[0][pk_field],
              data: data.results[0]
            };

            // Run custom callback for this field (if provided)
            if (definition.onValueChange) {
              definition.onValueChange(
                data.results[0][pk_field],
                data.results[0]
              );
            }

            onChange(value);
            setInitialData(value);
            dataRef.current = [value];
          }
        }
      });
  }, [
    autoFilled,
    definition.autoFill,
    definition.api_url,
    definition.filters,
    definition.pk_field,
    field.value
  ]);

  // If an initial value is provided, load from the API
  useEffect(() => {
    // If the value is unchanged, do nothing
    if (field.value === pk) return;

    const id = pk || field.value;

    if (id !== null && id !== undefined && id !== '') {
      fetchSingleField(id);
    } else {
      setPk(null);
    }
  }, [
    definition.api_url,
    definition.filters,
    definition.pk_field,
    field.value
  ]);

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

      const params = {
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

          results.forEach((item: any) => {
            const pk_field = definition.pk_field ?? 'pk';
            const pk = item[pk_field];

            if (pk && !alreadyPresentPks.includes(pk)) {
              values.push({
                value: pk,
                data: item
              });
            }
          });

          setData(values);
          dataRef.current = values;
          return response;
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
      const _pk = value?.value ?? null;
      field.onChange(_pk);

      setPk(_pk);

      // Run custom callback for this field (if provided)
      definition.onValueChange?.(_pk, value?.data ?? {});
    },
    [field.onChange, definition]
  );

  /* Construct a "cut-down" version of the definition,
   * which does not include any attributes that the lower components do not recognize
   */
  const fieldDefinition = useMemo(() => {
    return {
      ...definition,
      autoFill: undefined,
      modelRenderer: undefined,
      onValueChange: undefined,
      adjustFilters: undefined,
      exclude: undefined,
      read_only: undefined
    };
  }, [definition]);

  const currentValue = useMemo(() => {
    if (!pk) {
      return null;
    }

    const _data = [...data, initialData];
    return _data.find((item) => item.value === pk);
  }, [pk, data]);

  // Field doesn't follow Mantine theming
  // Define color theme to pass to field based on Mantine theme
  const theme = useMantineTheme();
  const { colorScheme } = useMantineColorScheme();

  const colors = useMemo(() => {
    let colors: any;
    if (colorScheme === 'dark') {
      colors = {
        neutral0: vars.colors.dark[6],
        neutral5: vars.colors.dark[4],
        neutral10: vars.colors.dark[4],
        neutral20: vars.colors.dark[4],
        neutral30: vars.colors.dark[3],
        neutral40: vars.colors.dark[2],
        neutral50: vars.colors.dark[1],
        neutral60: vars.colors.dark[0],
        neutral70: vars.colors.dark[0],
        neutral80: vars.colors.dark[0],
        neutral90: vars.colors.dark[0],
        primary: vars.colors.primaryColors[7],
        primary25: vars.colors.primaryColors[6],
        primary50: vars.colors.primaryColors[5],
        primary75: vars.colors.primaryColors[4]
      };
    } else {
      colors = {
        neutral0: vars.colors.white,
        neutral5: darken(vars.colors.white, 0.05),
        neutral10: darken(vars.colors.white, 0.1),
        neutral20: darken(vars.colors.white, 0.2),
        neutral30: darken(vars.colors.white, 0.3),
        neutral40: darken(vars.colors.white, 0.4),
        neutral50: darken(vars.colors.white, 0.5),
        neutral60: darken(vars.colors.white, 0.6),
        neutral70: darken(vars.colors.white, 0.7),
        neutral80: darken(vars.colors.white, 0.8),
        neutral90: darken(vars.colors.white, 0.9),
        primary: vars.colors.primaryColors[7],
        primary25: vars.colors.primaryColors[4],
        primary50: vars.colors.primaryColors[5],
        primary75: vars.colors.primaryColors[6]
      };
    }
    return colors;
  }, [theme]);

  return (
    <Input.Wrapper
      {...fieldDefinition}
      error={definition.error ?? error?.message}
      styles={{ description: { paddingBottom: '5px' } }}
    >
      <Group justify='space-between' wrap='nowrap' gap={3}>
        <Expand>
          <Select
            id={fieldId}
            aria-label={`related-field-${field.name}`}
            value={currentValue}
            ref={field.ref}
            options={data}
            filterOption={null}
            onInputChange={(value: any) => {
              setValue(value);
            }}
            onChange={onChange}
            onMenuScrollToBottom={() => setOffset(offset + limit)}
            onMenuOpen={() => {
              setIsOpen(true);
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
            placeholder={definition.placeholder || `${t`Search`}...`}
            loadingMessage={() => `${t`Loading`}...`}
            menuPortalTarget={document.body}
            noOptionsMessage={() => t`No results found`}
            menuPosition='fixed'
            styles={{
              menuPortal: (base: any) => ({ ...base, zIndex: 9999 }),
              clearIndicator: (base: any) => ({
                ...base,
                color: 'red',
                ':hover': { color: 'red' }
              })
            }}
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
        </Expand>
        {addBarcodeField && (
          <ScanButton
            modelType={definition.model}
            onScanSuccess={onBarcodeScan}
          />
        )}
      </Group>
    </Input.Wrapper>
  );
}
