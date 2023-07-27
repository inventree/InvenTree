import {
  Alert,
  Divider,
  LoadingOverlay,
  Modal,
  ScrollArea
} from '@mantine/core';
import { Button, Group, Loader, Stack } from '@mantine/core';
import { useForm } from '@mantine/form';
import { IconAlertCircle } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { AxiosResponse } from 'axios';
import { useEffect } from 'react';
import { useState } from 'react';

import { api } from '../../App';
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
  opened: boolean;
  preFormContent?: JSX.Element;
  preFormContentFunc?: () => JSX.Element;
  postFormContent?: JSX.Element;
  postFormContentFunc?: () => JSX.Element;
  onClose?: () => void;
  onFormSuccess?: () => void;
  onFormError?: () => void;
}

/**
 * An ApiForm component is a modal form which is rendered dynamically,
 * based on an API endpoint.

 */
export function ApiForm(props: ApiFormProps) {
  // Form state
  const form = useForm({});

  // Form field definitions (via API)
  const [fieldDefinitions, setFieldDefinitions] = useState<ApiFormFieldType[]>(
    []
  );

  // Error observed during form construction
  const [error, setError] = useState<string>('');

  // Query manager for retrieving form definition from the server
  const definitionQuery = useQuery({
    enabled: props.opened && !!props.url,
    queryKey: ['form-definition', name, props.url, props.pk],
    queryFn: async () => {
      // Clear form construction error field
      setError('');
      return api
        .options(getUrl())
        .then((response) => {
          setFieldDefinitions(extractFieldDefinitions(response));
          return response;
        })
        .catch((error) => {
          setError(error.message);
          setFieldDefinitions([]);
        });
    }
  });

  // Query manager for retrieiving initial data from the server
  const initialDataQuery = useQuery({
    enabled:
      props.fetchInitialData &&
      props.opened &&
      !!props.url &&
      fieldDefinitions.length > 0,
    queryKey: ['form-initial-data', name, props.url, props.pk],
    queryFn: async () => {
      return api
        .get(getUrl())
        .then((response) => {
          form.setValues(response.data);
          return response;
        })
        .catch((error) => {
          console.error('Error fetching initial data:', error);
          setError(error.message);
        });
    }
  });

  // State variable to determine if the form can render the data
  const [canRender, setCanRender] = useState<boolean>(false);

  // Update the canRender state variable on status change
  useEffect(() => {
    setCanRender(
      !definitionQuery.isFetching && definitionQuery.isSuccess && !error
    );
  }, [definitionQuery, error]);

  // State variable to determine if the form can be submitted
  const [canSubmit, setCanSubmit] = useState<boolean>(false);

  // Update the canSubmit state variable on status change
  useEffect(() => {
    setCanSubmit(canRender && true);
    // TODO: This will be updated when we have a query manager for form submission
  }, [canRender]);

  // Construct a fully-qualified URL based on the provided details
  function getUrl(): string {
    if (!props.url) {
      return '';
    }

    let u = props.url;

    if (props.pk && props.pk > 0) {
      u += `${props.pk}/`;
    }

    return u;
  }

  /**
   * Extract a list of field definitions from an API response.
   * @param response : The API response to extract the field definitions from.
   * @returns A list of field definitions.
   */
  function extractFieldDefinitions(
    response: AxiosResponse
  ): ApiFormFieldType[] {
    if (!props.method) {
      return [];
    }

    let actions = response.data?.actions[props.method.toUpperCase()] || [];

    if (actions.length == 0) {
      setError(`Permission denied for ${props.method} at ${props.url}`);
      return [];
    }

    let definitions: ApiFormFieldType[] = [];

    for (const fieldName in actions) {
      const field = actions[fieldName];
      definitions.push({
        name: fieldName,
        label: field.label,
        description: field.help_text,
        value: field.value || field.default,
        fieldType: field.type,
        required: field.required,
        placeholder: field.placeholder,
        api_url: field.api_url,
        model: field.model
      });
    }

    return definitions;
  }

  return (
    <Modal
      size="xl"
      radius="sm"
      opened={props.opened}
      onClose={() => {
        props.onClose ? props.onClose() : null;
      }}
      title={props.title}
    >
      <Stack>
        <Divider />
        <Stack>
          <LoadingOverlay
            visible={definitionQuery.isFetching || initialDataQuery.isFetching}
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
          {props.preFormContent && props.preFormContent}
          {props.preFormContentFunc ? props.preFormContentFunc() : null}
          {canRender && (
            <ScrollArea>
              <Stack spacing="md">
                {props.fields.map((field) => (
                  <ApiFormField
                    key={field.name}
                    field={field}
                    form={form}
                    definitions={fieldDefinitions}
                    onValueChange={(fieldName, value) => {
                      form.setValues({ [fieldName]: value });
                    }}
                  />
                ))}
              </Stack>
            </ScrollArea>
          )}
          {props.postFormContent && props.postFormContent}
          {props.postFormContentFunc ? props.postFormContentFunc() : null}
        </Stack>
        <Divider />
        <Group position="right">
          <Button
            onClick={props.onClose}
            variant="outline"
            radius="sm"
            color={props.cancelColor ?? 'blue'}
          >
            {props.cancelText ?? `Cancel`}
          </Button>
          <Button
            onClick={() => null}
            variant="outline"
            radius="sm"
            color={props.submitColor ?? 'green'}
            disabled={!canSubmit}
          >
            <Group position="right" spacing={5} noWrap={true}>
              <Loader size="xs" />
              {props.submitText ?? `Submit`}
            </Group>
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
