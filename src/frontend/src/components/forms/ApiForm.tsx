import { t } from '@lingui/macro';
import {
  Alert,
  Button,
  DefaultMantineColor,
  Divider,
  Group,
  LoadingOverlay,
  Paper,
  Stack,
  Text
} from '@mantine/core';
import { useId } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  FieldValues,
  FormProvider,
  SubmitErrorHandler,
  SubmitHandler,
  useForm
} from 'react-hook-form';
import { useNavigate } from 'react-router-dom';

import { api, queryClient } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import {
  NestedDict,
  constructField,
  constructFormUrl,
  extractAvailableFields,
  mapFields
} from '../../functions/forms';
import { invalidResponse } from '../../functions/notifications';
import { getDetailUrl } from '../../functions/urls';
import { TableState } from '../../hooks/UseTable';
import { PathParams } from '../../states/ApiState';
import { Boundary } from '../Boundary';
import {
  ApiFormField,
  ApiFormFieldSet,
  ApiFormFieldType
} from './fields/ApiFormField';

export interface ApiFormAction {
  text: string;
  variant?: 'outline';
  color?: DefaultMantineColor;
  onClick: () => void;
}

/**
 * Properties for the ApiForm component
 * @param url : The API endpoint to fetch the form data from
 * @param pk : Optional primary-key value when editing an existing object
 * @param pk_field : Optional primary-key field name (default: pk)
 * @param pathParams : Optional path params for the url
 * @param method : Optional HTTP method to use when submitting the form (default: GET)
 * @param fields : The fields to render in the form
 * @param submitText : Optional custom text to display on the submit button (default: Submit)4
 * @param submitColor : Optional custom color for the submit button (default: green)
 * @param fetchInitialData : Optional flag to fetch initial data from the server (default: true)
 * @param preFormContent : Optional content to render before the form fields
 * @param postFormContent : Optional content to render after the form fields
 * @param successMessage : Optional message to display on successful form submission
 * @param onFormSuccess : A callback function to call when the form is submitted successfully.
 * @param onFormError : A callback function to call when the form is submitted with errors.
 * @param modelType : Define a model type for this form
 * @param follow : Boolean, follow the result of the form (if possible)
 * @param table : Table to update on success (if provided)
 */
export interface ApiFormProps {
  url: ApiEndpoints | string;
  pk?: number | string | undefined;
  pk_field?: string;
  pathParams?: PathParams;
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  fields?: ApiFormFieldSet;
  focus?: string;
  initialData?: FieldValues;
  submitText?: string;
  submitColor?: string;
  fetchInitialData?: boolean;
  ignorePermissionCheck?: boolean;
  preFormContent?: JSX.Element;
  preFormWarning?: string;
  preFormSuccess?: string;
  postFormContent?: JSX.Element;
  successMessage?: string;
  onFormSuccess?: (data: any) => void;
  onFormError?: () => void;
  table?: TableState;
  modelType?: ModelType;
  follow?: boolean;
  actions?: ApiFormAction[];
  timeout?: number;
}

export function OptionsApiForm({
  props: _props,
  id: pId
}: {
  props: ApiFormProps;
  id?: string;
}) {
  const props = useMemo(
    () => ({
      ..._props,
      method: _props.method || 'GET'
    }),
    [_props]
  );

  const id = useId(pId);

  const url = useMemo(
    () => constructFormUrl(props.url, props.pk, props.pathParams),
    [props.url, props.pk, props.pathParams]
  );

  const optionsQuery = useQuery({
    enabled: true,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    queryKey: [
      'form-options-data',
      id,
      props.method,
      props.url,
      props.pk,
      props.pathParams
    ],
    queryFn: async () => {
      let response = await api.options(url);
      let fields: Record<string, ApiFormFieldType> | null = {};
      if (!props.ignorePermissionCheck) {
        fields = extractAvailableFields(response, props.method);
      }
      return fields;
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

  const formProps: ApiFormProps = useMemo(() => {
    const _props = { ...props };

    if (!_props.fields) return _props;

    for (const [k, v] of Object.entries(_props.fields)) {
      _props.fields[k] = constructField({
        field: v,
        definition: optionsQuery?.data?.[k]
      });

      // If the user has specified initial data, use that value here
      let value = _props?.initialData?.[k];

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
      optionsLoading={optionsQuery.isFetching}
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
}: {
  id: string;
  props: ApiFormProps;
  optionsLoading: boolean;
}) {
  const navigate = useNavigate();

  const fields: ApiFormFieldSet = useMemo(() => {
    return props.fields ?? {};
  }, [props.fields]);

  const defaultValues: FieldValues = useMemo(() => {
    let defaultValuesMap = mapFields(fields ?? {}, (_path, field) => {
      return field.value ?? field.default ?? undefined;
    });

    // If the user has specified initial data, that overrides default values
    // But, *only* for the fields we have specified
    if (props.initialData) {
      Object.keys(props.initialData).map((key) => {
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
    () => constructFormUrl(props.url, props.pk, props.pathParams),
    [props.url, props.pk, props.pathParams]
  );

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
      try {
        // Await API call
        let response = await api.get(url);

        // Define function to process API response
        const processFields = (fields: ApiFormFieldSet, data: NestedDict) => {
          const res: NestedDict = {};

          // TODO: replace with .map()
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

        // Process API response
        const initialData: any = processFields(fields, response.data);

        // Update form values, but only for the fields specified for this form
        form.reset(initialData);

        // Update the field references, too
        Object.keys(fields).forEach((fieldName) => {
          if (fieldName in initialData) {
            let field = fields[fieldName] ?? {};
            fields[fieldName] = {
              ...field,
              value: initialData[fieldName]
            };
          }
        });

        return response;
      } catch (error) {
        console.error('ERR: Error fetching initial data:', error);
        // Re-throw error to allow react-query to handle error
        throw error;
      }
    }
  });

  // Fetch initial data on form load
  useEffect(() => {
    // Fetch initial data if the fetchInitialData property is set
    if (props.fetchInitialData) {
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
  }, [props.fetchInitialData]);

  const isLoading = useMemo(
    () =>
      isFormLoading ||
      initialDataQuery.isFetching ||
      optionsLoading ||
      isSubmitting ||
      !fields,
    [
      isFormLoading,
      initialDataQuery.isFetching,
      isSubmitting,
      fields,
      optionsLoading
    ]
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

        focusField = fieldName;
      });
    }

    if (isLoading || initialFocus == focusField) {
      return;
    }

    form.setFocus(focusField);
    setInitialFocus(focusField);
  }, [props.focus, fields, form.setFocus, isLoading, initialFocus]);

  const submitForm: SubmitHandler<FieldValues> = async (data) => {
    setNonFieldErrors([]);

    let method = props.method?.toLowerCase() ?? 'get';

    let hasFiles = false;
    mapFields(fields, (_path, field) => {
      if (field.field_type === 'file upload') {
        hasFiles = true;
      }
    });

    return api({
      method: method,
      url: url,
      data: data,
      timeout: props.timeout,
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
              props.onFormSuccess(response.data);
            }

            if (props.follow && props.modelType && response.data?.pk) {
              // If we want to automatically follow the returned data
              navigate(getDetailUrl(props.modelType, response.data?.pk));
            } else if (props.table) {
              // If we want to automatically update or reload a linked table
              let pk_field = props.pk_field ?? 'pk';

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
            props.onFormError?.();
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
                for (const [k, v] of Object.entries(errors)) {
                  const path = _path ? `${_path}.${k}` : k;

                  if (k === 'non_field_errors' || k === '__all__') {
                    if (Array.isArray(v)) {
                      _nonFieldErrors.push(...v);
                    }
                    continue;
                  }

                  if (typeof v === 'object' && Array.isArray(v)) {
                    form.setError(path, { message: v.join(', ') });
                  } else {
                    processErrors(v, path);
                  }
                }
              };

              processErrors(error.response.data);
              setNonFieldErrors(_nonFieldErrors);
              break;
            default:
              // Unexpected state on form error
              invalidResponse(error.response.status);
              props.onFormError?.();
              break;
          }
        } else {
          invalidResponse(0);
          props.onFormError?.();
        }

        return error;
      });
  };

  const onFormError = useCallback<SubmitErrorHandler<FieldValues>>(() => {
    props.onFormError?.();
  }, [props.onFormError]);

  return (
    <Stack>
      <Boundary label={`ApiForm-${id}`}>
        {/* Show loading overlay while fetching fields */}
        {/* zIndex used to force overlay on top of modal header bar */}
        <LoadingOverlay visible={isLoading} zIndex={1010} />

        {/* Attempt at making fixed footer with scroll area */}
        <Paper mah={'65vh'} style={{ overflowY: 'auto' }}>
          <div>
            {/* Form Fields */}
            <Stack gap="sm">
              {(!isValid || nonFieldErrors.length > 0) && (
                <Alert radius="sm" color="red" title={t`Error`}>
                  {nonFieldErrors.length > 0 && (
                    <Stack gap="xs">
                      {nonFieldErrors.map((message) => (
                        <Text key={message}>{message}</Text>
                      ))}
                    </Stack>
                  )}
                </Alert>
              )}
              <Boundary label={`ApiForm-${id}-PreFormContent`}>
                {props.preFormContent}
                {props.preFormSuccess && (
                  <Alert color="green" radius="sm">
                    {props.preFormSuccess}
                  </Alert>
                )}
                {props.preFormWarning && (
                  <Alert color="orange" radius="sm">
                    {props.preFormWarning}
                  </Alert>
                )}
              </Boundary>
              <Boundary label={`ApiForm-${id}-FormContent`}>
                <FormProvider {...form}>
                  <Stack gap="xs">
                    {!optionsLoading &&
                      Object.entries(fields).map(([fieldName, field]) => (
                        <ApiFormField
                          key={fieldName}
                          fieldName={fieldName}
                          definition={field}
                          control={form.control}
                        />
                      ))}
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
          <Group justify="right">
            {props.actions?.map((action, i) => (
              <Button
                key={i}
                onClick={action.onClick}
                variant={action.variant ?? 'outline'}
                radius="sm"
                color={action.color}
              >
                {action.text}
              </Button>
            ))}
            <Button
              onClick={form.handleSubmit(submitForm, onFormError)}
              variant="filled"
              radius="sm"
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
}: {
  id?: string;
  props: ApiFormProps;
}) {
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
}: {
  id?: string;
  props: ApiFormProps;
}) {
  const editProps = useMemo<ApiFormProps>(
    () => ({
      ...props,
      fetchInitialData: props.fetchInitialData ?? true,
      submitText: t`Update` ?? props.submitText,
      method: 'PUT'
    }),
    [props]
  );

  return <OptionsApiForm props={editProps} id={id} />;
}

export function DeleteApiForm({
  id,
  props
}: {
  id?: string;
  props: ApiFormProps;
}) {
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
