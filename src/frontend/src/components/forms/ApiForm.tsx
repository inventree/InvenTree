import { t } from '@lingui/core/macro';
import {
  Alert,
  Button,
  Divider,
  Group,
  LoadingOverlay,
  Paper,
  Stack,
  Text
} from '@mantine/core';
import { useId } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  type FieldValues,
  FormProvider,
  type SubmitErrorHandler,
  type SubmitHandler,
  useForm
} from 'react-hook-form';
import { type NavigateFunction, useNavigate } from 'react-router-dom';

import { isTrue } from '@lib/functions/Conversion';
import { getDetailUrl } from '@lib/functions/Navigation';
import type {
  ApiFormFieldSet,
  ApiFormFieldType,
  ApiFormProps
} from '@lib/types/Forms';
import { useApi } from '../../contexts/ApiContext';
import {
  type NestedDict,
  constructField,
  constructFormUrl,
  extractAvailableFields,
  mapFields
} from '../../functions/forms';
import {
  invalidResponse,
  showTimeoutNotification
} from '../../functions/notifications';
import { Boundary } from '../Boundary';
import { ApiFormField } from './fields/ApiFormField';

export function OptionsApiForm({
  props: _props,
  opened,
  id: pId
}: Readonly<{
  props: ApiFormProps;
  opened?: boolean;
  id?: string;
}>) {
  const api = useApi();

  const props = useMemo(
    () => ({
      ..._props,
      method: _props.method || 'GET'
    }),
    [_props]
  );

  const id = useId(pId);

  const url = useMemo(
    () =>
      constructFormUrl(
        props.url,
        props.pk,
        props.pathParams,
        props.queryParams
      ),
    [props.url, props.pk, props.pathParams, props.queryParams]
  );

  const optionsQuery = useQuery({
    enabled: opened !== false && props.ignorePermissionCheck !== true,
    refetchOnMount: false,
    queryKey: [
      'form-options-data',
      id,
      opened,
      props.ignorePermissionCheck,
      props.method,
      props.url,
      props.pk,
      props.pathParams
    ],
    queryFn: async () => {
      if (props.ignorePermissionCheck === true || opened === false) {
        return {};
      }

      return api.options(url).then((response: any) => {
        return extractAvailableFields(response, props.method);
      });
    },
    throwOnError: (error: any) => {
      if (error.response) {
        invalidResponse(error.response.status);
      } else {
        notifications.hide('form-error');
        notifications.show({
          title: t`Form Error`,
          message: error.message,
          color: 'red',
          id: 'form-error'
        });
      }
      return false;
    }
  });

  // Refetch form options whenever the modal is opened
  useEffect(() => {
    if (opened !== false) {
      optionsQuery.refetch();
    }
  }, [opened]);

  const formProps: ApiFormProps = useMemo(() => {
    const _props = { ...props };

    if (!_props.fields) return _props;

    _props.fields = { ..._props.fields };

    for (const [k, v] of Object.entries(_props.fields)) {
      _props.fields[k] = constructField({
        field: v,
        definition: optionsQuery?.data?.[k]
      });

      // If the user has specified initial data, use that value here
      const value = _props?.initialData?.[k];

      if (value) {
        _props.fields[k].value = value;
      }
    }

    return _props;
  }, [optionsQuery.data, props]);

  return (
    <ApiForm
      id={id}
      props={formProps}
      optionsLoading={optionsQuery.isFetching || !optionsQuery.data}
    />
  );
}

/**
 * An ApiForm component is a modal form which is rendered dynamically,
 * based on an API endpoint.
 */
export function ApiForm({
  id,
  props,
  optionsLoading
}: Readonly<{
  id: string;
  props: ApiFormProps;
  optionsLoading: boolean;
}>) {
  const api = useApi();
  const queryClient = useQueryClient();

  // Accessor for the navigation function (which is used to redirect the user)
  let navigate: NavigateFunction | null = null;

  try {
    navigate = useNavigate();
  } catch (_error) {
    // Note: If we launch a form within a plugin context, useNavigate() may not be available
    navigate = null;
  }

  const [fields, setFields] = useState<ApiFormFieldSet>(
    () => props.fields ?? {}
  );

  const defaultValues: FieldValues = useMemo(() => {
    const defaultValuesMap = mapFields(props.fields ?? {}, (_path, field) => {
      if (field.value !== undefined && field.value !== null) {
        return field.value;
      }
      if (field.default !== undefined && field.default !== null) {
        return field.default;
      }
      return undefined;
    });

    // If the user has specified initial data, that overrides default values
    // But, *only* for the fields we have specified
    if (props.initialData) {
      Object.keys(props.initialData).forEach((key) => {
        if (key in defaultValuesMap) {
          defaultValuesMap[key] =
            props?.initialData?.[key] ?? defaultValuesMap[key];
        }
      });
    }
    return defaultValuesMap;
  }, [props.fields, props.initialData]);

  // Form errors which are not associated with a specific field
  const [nonFieldErrors, setNonFieldErrors] = useState<string[]>([]);

  // Form state
  const form = useForm({
    criteriaMode: 'all',
    defaultValues
  });

  const {
    isValid,
    isDirty,
    isLoading: isFormLoading,
    isSubmitting
  } = form.formState;

  // Cache URL
  const url = useMemo(
    () =>
      constructFormUrl(
        props.url,
        props.pk,
        props.pathParams,
        props.queryParams
      ),
    [props.url, props.pk, props.pathParams]
  );

  // Define function to process API response
  const processFields = (fields: ApiFormFieldSet, data: NestedDict) => {
    const res: NestedDict = {};

    for (const [k, field] of Object.entries(fields)) {
      const dataValue = data[k];

      if (
        field.field_type === 'nested object' &&
        field.children &&
        typeof dataValue === 'object'
      ) {
        res[k] = processFields(field.children, dataValue);
      } else {
        res[k] = dataValue;

        if (field.onValueChange) {
          field.onValueChange(dataValue, data);
        }
      }
    }

    return res;
  };

  // Query manager for retrieving initial data from the server
  const initialDataQuery = useQuery({
    enabled: false,
    queryKey: [
      'form-initial-data',
      id,
      props.method,
      props.url,
      props.pk,
      props.pathParams
    ],
    queryFn: async () => {
      return await api.get(url).then((response: any) => {
        // Process API response
        const fetchedData: any = processFields(fields, response.data);

        // Update form values, but only for the fields specified for this form
        form.reset(fetchedData);
        return fetchedData;
      });
    }
  });

  useEffect(() => {
    const _fields: any = props.fields || {};
    const _initialData: any = props.initialData || {};
    const _fetchedData: any = initialDataQuery.data || {};

    for (const k of Object.keys(_fields)) {
      // Ensure default values override initial field spec
      if (k in defaultValues) {
        _fields[k].value = defaultValues[k];
      }

      // Ensure initial data overrides default values
      if (_initialData && k in _initialData) {
        _fields[k].value = _initialData[k];
      }

      // Ensure fetched data overrides also
      if (_fetchedData && k in _fetchedData) {
        _fields[k].value = _fetchedData[k];
      }
    }

    setFields(_fields);
  }, [props.fields, props.initialData, defaultValues, initialDataQuery.data]);

  // Fetch initial data on form load
  useEffect(() => {
    // Fetch initial data if the fetchInitialData property is set
    if (!optionsLoading && props.fetchInitialData) {
      queryClient.removeQueries({
        queryKey: [
          'form-initial-data',
          id,
          props.method,
          props.url,
          props.pk,
          props.pathParams
        ]
      });
      initialDataQuery.refetch();
    }
  }, [props.fetchInitialData, optionsLoading]);

  const isLoading: boolean = useMemo(
    () =>
      isFormLoading ||
      initialDataQuery.isFetching ||
      optionsLoading ||
      isSubmitting ||
      !fields,
    [isFormLoading, initialDataQuery, isSubmitting, fields, optionsLoading]
  );

  const [initialFocus, setInitialFocus] = useState<string>('');

  // Update field focus when the form is loaded
  useEffect(() => {
    let focusField = props.focus ?? '';

    if (!focusField) {
      // If a focus field is not specified, then focus on the first available field
      Object.entries(fields).forEach(([fieldName, field]) => {
        if (focusField || field.read_only || field.disabled || field.hidden) {
          return;
        }

        // Do not auto-focus on a 'choice' field
        if (field.field_type == 'choice') {
          return;
        }

        focusField = fieldName;
      });
    }

    if (isLoading) {
      return;
    }

    form.setFocus(focusField);
    setInitialFocus(focusField);
  }, [props.focus, form.setFocus, isLoading, initialFocus]);

  const submitForm: SubmitHandler<FieldValues> = async (data) => {
    setNonFieldErrors([]);

    const method = props.method?.toLowerCase() ?? 'get';

    let hasFiles = false;

    let jsonData = { ...data };
    const formData = new FormData();

    Object.keys(data).forEach((key: string) => {
      let value: any = data[key];
      const field: ApiFormFieldType = fields[key] ?? {};
      const field_type = field?.field_type;
      const exclude = field?.exclude;

      if (field_type == 'file upload' && !!value) {
        hasFiles = true;
      }

      // Special consideration for various field types
      switch (field_type) {
        case 'boolean':
          // Ensure boolean values are actually boolean
          value = isTrue(value) || false;
          break;
        case 'string':
          // Replace null string values with an empty string
          if (value === null && field?.allow_null == false) {
            value = '';
            jsonData[key] = value;
          }
          break;
        default:
          break;
      }

      // Stringify any JSON objects
      if (typeof value === 'object') {
        switch (field_type) {
          case 'file upload':
            break;
          default:
            if (value !== null && value !== undefined) {
              value = JSON.stringify(value);
            }
            break;
        }
      }

      if (exclude) {
        // Remove the field from the data
        delete jsonData[key];
      } else if (value != undefined) {
        formData.append(key, value);
      }
    });

    // Optionally pre-process the data before submitting it
    if (props.processFormData) {
      jsonData = props.processFormData(jsonData, form);
    }

    /* Set the timeout for the request:
     * - If a timeout is provided in the props, use that
     * - If the form contains files, use a longer timeout
     * - Otherwise, use the default timeout
     */
    const timeout = props.timeout ?? (hasFiles ? 30000 : undefined);

    return api({
      method: method,
      url: url,
      params: method.toLowerCase() == 'get' ? jsonData : undefined,
      data: hasFiles ? formData : jsonData,
      timeout: timeout,
      headers: {
        'Content-Type': hasFiles ? 'multipart/form-data' : 'application/json'
      }
    })
      .then((response) => {
        switch (response.status) {
          case 200:
          case 201:
          case 204:
            // Form was submitted successfully

            if (props.onFormSuccess) {
              // A custom callback hook is provided
              props.onFormSuccess(response.data, form);
            }

            if (props.follow && props.modelType && response.data?.pk) {
              // If we want to automatically follow the returned data
              if (!!navigate) {
                navigate(getDetailUrl(props.modelType, response.data?.pk));
              }
            } else if (props.table) {
              // If we want to automatically update or reload a linked table
              const pk_field = props.pk_field ?? 'pk';

              if (props.pk && response?.data[pk_field]) {
                props.table.updateRecord(response.data);
              } else {
                props.table.refreshTable();
              }
            }

            // Optionally show a success message
            if (props.successMessage) {
              notifications.hide('form-success');

              notifications.show({
                id: 'form-success',
                title: t`Success`,
                message: props.successMessage,
                color: 'green'
              });
            }

            break;
          default:
            // Unexpected state on form success
            invalidResponse(response.status);
            props.onFormError?.(response, form);
            break;
        }

        return response;
      })
      .catch((error) => {
        if (error.response) {
          switch (error.response.status) {
            case 400:
              // Data validation errors
              const _nonFieldErrors: string[] = [];

              const processErrors = (errors: any, _path?: string) => {
                // Handle an array of errors
                if (Array.isArray(errors)) {
                  errors.forEach((error: any) => {
                    _nonFieldErrors.push(error.toString());
                  });
                  return;
                }

                // Handle simple string
                if (typeof errors === 'string') {
                  _nonFieldErrors.push(errors);
                  return;
                }

                for (const [k, v] of Object.entries(errors)) {
                  const path = _path ? `${_path}.${k}` : k;

                  // Determine if field "k" is valid (exists and is visible)
                  const field = fields[k];
                  const valid = field && !field.hidden;

                  if (!valid || k == 'non_field_errors' || k == '__all__') {
                    processErrors(v);
                    continue;
                  }

                  if (typeof v === 'object' && Array.isArray(v)) {
                    if (field?.field_type == 'table') {
                      // Special handling for "table" fields - they have nested errors
                      v.forEach((item: any, idx: number) => {
                        for (const [key, value] of Object.entries(item)) {
                          const path: string = `${k}.${idx}.${key}`;
                          if (Array.isArray(value)) {
                            form.setError(path, { message: value.join(', ') });
                          }
                        }
                      });
                    } else {
                      // Standard error handling for other fields
                      form.setError(path, { message: v.join(', ') });
                    }
                  } else if (typeof v === 'string') {
                    form.setError(path, { message: v });
                  } else {
                    processErrors(v, path);
                  }
                }
              };

              processErrors(error.response.data);
              setNonFieldErrors(_nonFieldErrors);
              props.onFormError?.(error, form);

              break;
            default:
              // Unexpected state on form error
              invalidResponse(error.response.status);
              props.onFormError?.(error, form);
              break;
          }
        } else {
          showTimeoutNotification();
          props.onFormError?.(error, form);
        }

        return error;
      });
  };

  const onFormError = useCallback<SubmitErrorHandler<FieldValues>>(
    (error: any) => {
      props.onFormError?.(error, form);
    },
    [props.onFormError]
  );

  if (optionsLoading || initialDataQuery.isFetching) {
    return (
      <Paper mah={'65vh'}>
        <LoadingOverlay visible zIndex={1010} />
      </Paper>
    );
  }

  return (
    <Stack>
      <Boundary label={`ApiForm-${id}`}>
        {/* Show loading overlay while fetching fields */}
        {/* zIndex used to force overlay on top of modal header bar */}
        <LoadingOverlay visible={isLoading} zIndex={1010} />

        {/* Attempt at making fixed footer with scroll area */}
        <Paper
          mah={'65vh'}
          style={{
            overflowY: 'auto',
            paddingRight: '15px',
            paddingBottom: '10px',
            paddingLeft: '5px'
          }}
        >
          <div>
            {/* Form Fields */}
            <Stack gap='sm'>
              {(!isValid || nonFieldErrors.length > 0) && (
                <Alert radius='sm' color='red' title={t`Form Error`}>
                  {nonFieldErrors.length > 0 ? (
                    <Stack gap='xs'>
                      {nonFieldErrors
                        .filter((message) => !!message && message !== 'None')
                        .map((message) => (
                          <Text key={message}>{message}</Text>
                        ))}
                    </Stack>
                  ) : (
                    <Text>{t`Errors exist for one or more form fields`}</Text>
                  )}
                </Alert>
              )}
              <Boundary label={`ApiForm-${id}-PreFormContent`}>
                {props.preFormContent}
                {props.preFormSuccess && (
                  <Alert color='green' radius='sm'>
                    {props.preFormSuccess}
                  </Alert>
                )}
                {props.preFormWarning && (
                  <Alert color='orange' radius='sm'>
                    {props.preFormWarning}
                  </Alert>
                )}
              </Boundary>
              <Boundary label={`ApiForm-${id}-FormContent`}>
                <FormProvider {...form}>
                  <Stack gap='xs'>
                    {Object.entries(fields).map(([fieldName, field]) => {
                      return (
                        <ApiFormField
                          key={fieldName}
                          fieldName={fieldName}
                          definition={field}
                          control={form.control}
                          url={url}
                          setFields={setFields}
                          onKeyDown={(value) => {
                            if (
                              value == 'Enter' &&
                              !isLoading &&
                              (!props.fetchInitialData || isDirty)
                            ) {
                              form.handleSubmit(submitForm, onFormError)();
                            }
                          }}
                        />
                      );
                    })}
                  </Stack>
                </FormProvider>
              </Boundary>
              <Boundary label={`ApiForm-${id}-PostFormContent`}>
                {props.postFormContent}
              </Boundary>
            </Stack>
          </div>
        </Paper>

        {/* Footer with Action Buttons */}
        <Divider />
        <div>
          <Group justify='right'>
            {props.actions?.map((action, i) => (
              <Button
                key={`${i}-${action.text}`}
                onClick={action.onClick}
                variant={action.variant ?? 'outline'}
                radius='sm'
                color={action.color}
              >
                {action.text}
              </Button>
            ))}
            <Button
              onClick={form.handleSubmit(submitForm, onFormError)}
              variant='filled'
              radius='sm'
              color={props.submitColor ?? 'green'}
              disabled={isLoading || (props.fetchInitialData && !isDirty)}
            >
              {props.submitText ?? t`Submit`}
            </Button>
          </Group>
        </div>
      </Boundary>
    </Stack>
  );
}

export function CreateApiForm({
  id,
  props
}: Readonly<{
  id?: string;
  props: ApiFormProps;
}>) {
  const createProps = useMemo<ApiFormProps>(
    () => ({
      ...props,
      method: 'POST'
    }),
    [props]
  );

  return <OptionsApiForm props={createProps} id={id} />;
}

export function EditApiForm({
  id,
  props
}: Readonly<{
  id?: string;
  props: ApiFormProps;
}>) {
  const editProps = useMemo<ApiFormProps>(
    () => ({
      ...props,
      fetchInitialData: props.fetchInitialData ?? true,
      submitText: props.submitText ?? t`Update`,
      method: 'PUT'
    }),
    [props]
  );

  return <OptionsApiForm props={editProps} id={id} />;
}

export function DeleteApiForm({
  id,
  props
}: Readonly<{
  id?: string;
  props: ApiFormProps;
}>) {
  const deleteProps = useMemo<ApiFormProps>(
    () => ({
      ...props,
      method: 'DELETE',
      submitText: t`Delete`,
      submitColor: 'red',
      fields: {}
    }),
    [props]
  );

  return <OptionsApiForm props={deleteProps} id={id} />;
}
