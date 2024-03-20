import { t } from '@lingui/macro';
import {
  Alert,
  DefaultMantineColor,
  LoadingOverlay,
  Paper,
  Text
} from '@mantine/core';
import { Button, Group, Stack } from '@mantine/core';
import { useId } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useRef } from 'react';
import { useState } from 'react';
import {
  FieldValues,
  FormProvider,
  SubmitErrorHandler,
  SubmitHandler,
  useForm
} from 'react-hook-form';

import { api, queryClient } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import {
  NestedDict,
  constructField,
  constructFormUrl,
  extractAvailableFields,
  mapFields
} from '../../functions/forms';
import { invalidResponse } from '../../functions/notifications';
import { PathParams } from '../../states/ApiState';
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
 */
export interface ApiFormProps {
  url: ApiEndpoints | string;
  pk?: number | string | undefined;
  pathParams?: PathParams;
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  fields?: ApiFormFieldSet;
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

  const { data } = useQuery({
    enabled: true,
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
        notifications.show({
          title: t`Form Error`,
          message: error.message,
          color: 'red'
        });
      }
      return false;
    }
  });

  const formProps: ApiFormProps = useMemo(() => {
    const _props = { ...props };

    // This forcefully overrides initial data
    // Currently, most modals do not get pre-loaded correctly
    if (!data) {
      _props.fields = undefined;
    }

    if (!_props.fields) return _props;

    for (const [k, v] of Object.entries(_props.fields)) {
      _props.fields[k] = constructField({
        field: v,
        definition: data?.[k]
      });

      // If the user has specified initial data, use that value here
      let value = _props?.initialData?.[k];

      if (value) {
        _props.fields[k].value = value;
      }
    }

    return _props;
  }, [data, props]);

  return <ApiForm id={id} props={formProps} />;
}

/**
 * An ApiForm component is a modal form which is rendered dynamically,
 * based on an API endpoint.
 */
export function ApiForm({ id, props }: { id: string; props: ApiFormProps }) {
  const defaultValues: FieldValues = useMemo(() => {
    let defaultValuesMap = mapFields(props.fields ?? {}, (_path, field) => {
      return field.value ?? field.default ?? undefined;
    });

    // If the user has specified initial data, use that instead
    if (props.initialData) {
      defaultValuesMap = {
        ...defaultValuesMap,
        ...props.initialData
      };
    }

    // Update the form values, but only for the fields specified for this form

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
            }
          }

          return res;
        };

        // Process API response
        const initialData: any = processFields(
          props.fields ?? {},
          response.data
        );

        // Update form values, but only for the fields specified for this form
        form.reset(initialData);

        return response;
      } catch (error) {
        console.error('Error fetching initial data:', error);
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
  }, []);

  const submitForm: SubmitHandler<FieldValues> = async (data) => {
    setNonFieldErrors([]);

    let method = props.method?.toLowerCase() ?? 'get';

    let hasFiles = false;
    mapFields(props.fields ?? {}, (_path, field) => {
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

            // Optionally call the onFormSuccess callback
            if (props.onFormSuccess) {
              props.onFormSuccess(response.data);
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

  const isLoading = useMemo(
    () =>
      isFormLoading ||
      initialDataQuery.isFetching ||
      isSubmitting ||
      !props.fields,
    [isFormLoading, initialDataQuery.isFetching, isSubmitting, props.fields]
  );

  const onFormError = useCallback<SubmitErrorHandler<FieldValues>>(() => {
    props.onFormError?.();
  }, [props.onFormError]);

  return (
    <Stack>
      {/* Attempt at making fixed footer with scroll area */}
      <Paper mah={'65vh'} style={{ overflowY: 'auto' }}>
        <div>
          {/* Form Fields */}
          <Stack spacing="sm">
            <LoadingOverlay visible={isLoading} />
            {(!isValid || nonFieldErrors.length > 0) && (
              <Alert radius="sm" color="red" title={t`Form Errors Exist`}>
                {nonFieldErrors.length > 0 && (
                  <Stack spacing="xs">
                    {nonFieldErrors.map((message) => (
                      <Text key={message}>{message}</Text>
                    ))}
                  </Stack>
                )}
              </Alert>
            )}
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
            <FormProvider {...form}>
              <Stack spacing="xs">
                {Object.entries(props.fields ?? {}).map(
                  ([fieldName, field]) => (
                    <ApiFormField
                      key={fieldName}
                      fieldName={fieldName}
                      definition={field}
                      control={form.control}
                    />
                  )
                )}
              </Stack>
            </FormProvider>
            {props.postFormContent}
          </Stack>
        </div>
      </Paper>

      {/* Footer with Action Buttons */}
      <div>
        <Group position="right">
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
