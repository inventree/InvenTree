import { t } from '@lingui/macro';
import {
  Alert,
  Divider,
  LoadingOverlay,
  ScrollArea,
  Text
} from '@mantine/core';
import { Button, Group, Stack } from '@mantine/core';
import { useForm } from '@mantine/form';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';
import { IconAlertCircle } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo } from 'react';
import { useState } from 'react';

import { api } from '../../App';
import { constructFormUrl } from '../../functions/forms';
import { invalidResponse } from '../../functions/notifications';
import { ApiFormField, ApiFormFieldType } from './fields/ApiFormField';

/**
 * Properties for the ApiForm component
 * @param name : The name (identifier) for this form
 * @param url : The API endpoint to fetch the form data from
 * @param pk : Optional primary-key value when editing an existing object
 * @param title : The title to display in the form header
 * @param fields : The fields to render in the form
 * @param submitText : Optional custom text to display on the submit button (default: Submit)4
 * @param submitColor : Optional custom color for the submit button (default: green)
 * @param cancelText : Optional custom text to display on the cancel button (default: Cancel)
 * @param cancelColor : Optional custom color for the cancel button (default: blue)
 * @param fetchInitialData : Optional flag to fetch initial data from the server (default: true)
 * @param method : Optional HTTP method to use when submitting the form (default: GET)
 * @param preFormContent : Optional content to render before the form fields
 * @param postFormContent : Optional content to render after the form fields
 * @param successMessage : Optional message to display on successful form submission
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
  successMessage?: string;
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

  // Render post-form content
  // TODO: Future work will allow this content to be updated dynamically based on the form data
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
  const [errorMessages, setErrorMessages] = useState<string[]>([]);

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
        });
    }
  });

  // Fetch initial data on form load
  useEffect(() => {
    // Provide initial form data
    props.fields.forEach((field) => {
      if (field.value !== undefined) {
        form.setValues({
          [field.name]: field.value
        });
      }
    });

    // Fetch initial data if the fetchInitialData property is set
    if (props.fetchInitialData) {
      initialDataQuery.refetch();
    }
  }, []);

  // Query manager for submitting data
  const submitQuery = useQuery({
    enabled: false,
    queryKey: ['form-submit', props.name, props.url, props.pk],
    queryFn: async () => {
      let method = props.method?.toLowerCase() ?? 'get';

      api({
        method: method,
        url: url,
        data: form.values
      })
        .then((response) => {
          switch (response.status) {
            case 200:
            case 201:
            case 204:
              // Form was submitted successfully

              // Optionally call the onFormSuccess callback
              if (props.onFormSuccess) {
                props.onFormSuccess();
              }

              // Optionally show a success message
              if (props.successMessage) {
                notifications.show({
                  title: t`Success`,
                  message: props.successMessage,
                  color: 'green'
                });
              }

              closeForm();
              break;
            default:
              // Unexpected state on form success
              invalidResponse(response.status);
              closeForm();
              break;
          }
        })
        .catch((error) => {
          if (error.response) {
            switch (error.response.status) {
              case 400:
                // Data validation error
                form.setErrors(error.response.data);
                break;
              default:
                // Unexpected state on form error
                invalidResponse(error.response.status);
                closeForm();
                break;
            }
          } else {
            invalidResponse(0);
            closeForm();
          }

          return error;
        });
    },
    refetchOnMount: false,
    refetchOnWindowFocus: false
  });

  // State variable to determine if the form can be submitted
  const [canSubmit, setCanSubmit] = useState<boolean>(false);

  // Update the canSubmit state variable on status change
  useEffect(() => {
    setCanSubmit(!submitQuery.isFetching);
  }, [submitQuery.isFetching]);

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
        {false && form.errors && (
          <Alert radius="sm" color="red" title={`Error`}>
            <Text>Form Errors Exist</Text>
          </Alert>
        )}
        {false && errorMessages && (
          <Alert
            radius="sm"
            color="red"
            title={`Error`}
            icon={<IconAlertCircle size="1rem" />}
          >
            <Stack spacing="xs">
              {errorMessages.map((message) => (
                <Text key={message}>{message}</Text>
              ))}
            </Stack>
          </Alert>
        )}
        {preFormElement}
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
          {props.cancelText ?? t`Cancel`}
        </Button>
        <Button
          onClick={submitForm}
          variant="outline"
          radius="sm"
          color={props.submitColor ?? 'green'}
          disabled={!canSubmit}
        >
          {props.submitText ?? t`Submit`}
        </Button>
      </Group>
    </Stack>
  );
}
