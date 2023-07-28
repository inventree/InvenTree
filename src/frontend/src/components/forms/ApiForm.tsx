import { jsx } from '@emotion/react';
import {
  Alert,
  Divider,
  LoadingOverlay,
  ScrollArea,
  Text
} from '@mantine/core';
import { Button, Group, Loader, Stack } from '@mantine/core';
import { useForm } from '@mantine/form';
import { modals } from '@mantine/modals';
import { IconAlertCircle } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { ReactNode, useEffect, useMemo } from 'react';
import { useState } from 'react';

import { api } from '../../App';
import { constructFormUrl } from '../../functions/forms';
import { ApiFormField, ApiFormFieldType } from './ApiFormField';

/**
 * Properties for the ApiForm component
 * @param url : The API endpoint to fetch the form from.
 * @param fields : The fields to render in the form.
 * @param opened : Whether the form is opened or not.
 * @param onClose : A callback function to call when the form is closed.
 * @param onFormSuccess : A callback function to call when the form is submitted successfully.
 * @param onFormError : A callback function to call when the form is submitted with errors.
 */
export interface ApiFormProps {
  name: string;
  url: string;
  pk?: number;
  title: string;
  fields: ApiFormFieldType[];
  cancelText?: string;
  submitText?: string;
  submitColor?: string;
  cancelColor?: string;
  fetchInitialData?: boolean;
  method?: string;
  preFormContent?: JSX.Element | (() => JSX.Element);
  postFormContent?: JSX.Element | (() => JSX.Element);
  onClose?: () => void;
  onFormSuccess?: () => void;
  onFormError?: () => void;
}

/**
 * An ApiForm component is a modal form which is rendered dynamically,
 * based on an API endpoint.
 */
export function ApiForm({
  modalId,
  props,
  fieldDefinitions = []
}: {
  modalId: string;
  props: ApiFormProps;
  fieldDefinitions: ApiFormFieldType[];
}) {
  // Form state
  const form = useForm({});

  // Cache URL
  const url = useMemo(() => constructFormUrl(props), [props]);

  // Render pre-form content
  // TODO: Future work will allow this content to be updated dynamically based on the form data
  const preFormElement: JSX.Element | null = useMemo(() => {
    if (props.preFormContent === undefined) {
      return null;
    } else if (props.preFormContent instanceof Function) {
      return props.preFormContent();
    } else {
      return props.preFormContent;
    }
  }, [props]);

  const postFormElement: JSX.Element | null = useMemo(() => {
    if (props.postFormContent === undefined) {
      return null;
    } else if (props.postFormContent instanceof Function) {
      return props.postFormContent();
    } else {
      return props.postFormContent;
    }
  }, [props]);

  // Error observed during form construction
  const [error, setError] = useState<string>('');

  // Query manager for retrieiving initial data from the server
  const initialDataQuery = useQuery({
    enabled: false,
    queryKey: ['form-initial-data', props.name, props.url, props.pk],
    queryFn: async () => {
      return api
        .get(url)
        .then((response) => {
          // Update form values, but only for the fields specified for the form
          props.fields.forEach((field) => {
            if (field.name in response.data) {
              form.setValues({
                [field.name]: response.data[field.name]
              });
            }
          });

          return response;
        })
        .catch((error) => {
          console.error('Error fetching initial data:', error);
          setError(error.message);
        });
    }
  });

  // Fetch initial data on form load
  useEffect(() => {
    if (props.fetchInitialData) {
      initialDataQuery.refetch();
    }
  }, []);

  // Query manager for submitting data
  const submitQuery = useQuery({
    enabled: false,
    queryKey: ['form-submit', props.name, props.url, props.pk],
    queryFn: async () => {
      switch (props.method?.toUpperCase()) {
        case 'PUT':
          return api
            .put(url, form.values)
            .then((response) => {
              console.log('response:', response.status, response.data);
              return response;
            })
            .catch((error) => {
              if (error.response) {
                switch (error.response.status) {
                  case 400:
                    console.log('400 error:', error.response.data);
                    form.setErrors(error.response.data);
                    // form.setErrors({
                    //   name: 'This field is required',
                    // });
                    break;
                  default:
                    // TODO:
                    break;
                }
              } else {
                console.error(
                  'put error:',
                  error.response.status,
                  error.response.data
                );
                // TODO: ???
              }

              return error;
            });
        default:
          console.log('unhandled form method:', props.method);
          return null;
      }
    },
    refetchOnMount: false,
    refetchOnWindowFocus: false
  });

  // State variable to determine if the form can render the data
  const [canRender, setCanRender] = useState<boolean>(false);

  // Update the canRender state variable on status change
  useEffect(() => {
    setCanRender(!error);
  }, [error]);

  // State variable to determine if the form can be submitted
  const [canSubmit, setCanSubmit] = useState<boolean>(false);

  // Update the canSubmit state variable on status change
  useEffect(() => {
    setCanSubmit(canRender && !submitQuery.isFetching);
    // TODO: This will be updated when we have a query manager for form submission
  }, [canRender]);

  /**
   * Callback to perform form submission
   */
  function submitForm() {
    submitQuery.refetch();
  }

  /**
   * Callback to close the form
   * Note that the calling function might implement an onClose() callback,
   * which will be automatically called
   */
  function closeForm() {
    modals.close(modalId);
  }

  return (
    <Stack>
      <Divider />
      <Stack spacing="sm">
        <LoadingOverlay
          visible={initialDataQuery.isFetching || submitQuery.isFetching}
        />
        {error && (
          <Alert
            radius="sm"
            color="red"
            title={`Error`}
            icon={<IconAlertCircle size="1rem" />}
          >
            {error}
          </Alert>
        )}
        {preFormElement}
        {canRender && (
          <ScrollArea>
            <Stack spacing="xs">
              {props.fields
                .filter((field) => !field.hidden)
                .map((field) => (
                  <ApiFormField
                    key={field.name}
                    field={field}
                    formProps={props}
                    form={form}
                    error={form.errors[field.name] ?? null}
                    definitions={fieldDefinitions}
                  />
                ))}
            </Stack>
          </ScrollArea>
        )}
        {postFormElement}
      </Stack>
      <Divider />
      <Group position="right">
        <Button
          onClick={closeForm}
          variant="outline"
          radius="sm"
          color={props.cancelColor ?? 'blue'}
        >
          {props.cancelText ?? `Cancel`}
        </Button>
        <Button
          onClick={submitForm}
          variant="outline"
          radius="sm"
          color={props.submitColor ?? 'green'}
          disabled={!canSubmit}
        >
          {props.submitText ?? `Submit`}
        </Button>
      </Group>
    </Stack>
  );
}
