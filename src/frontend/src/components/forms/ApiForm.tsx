import { t } from '@lingui/macro';
import { Alert, Divider, Modal, ScrollArea, TextInput } from '@mantine/core';
import { Button, Center, Group, Loader, Stack, Text } from '@mantine/core';
import { useForm } from '@mantine/form';
import { IconAlertCircle } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { AxiosResponse } from 'axios';
import { ReactNode, useEffect } from 'react';
import { useState } from 'react';
import { useMemo } from 'react';

import { api } from '../../App';

/* Definition of the ApiForm field component.
 * - The 'name' attribute *must* be provided
 * - All other attributes are optional, and may be provided by the API
 * - However, they can be overridden by the user
 */
export type ApiFormFieldType = {
  name: string;
  label?: string;
  value?: any;
  type?: string;
  required?: boolean;
  hidden?: boolean;
  disabled?: boolean;
  placeholder?: string;
  description?: string;
  icon?: ReactNode;
  errors?: string[];
  error?: any;
};

/**
 * Render an individual form field
 */
function ApiFormField({
  field,
  definitions
}: {
  field: ApiFormFieldType;
  definitions: ApiFormFieldType[];
}) {
  // Extract field definition from provided data
  // Where user has provided specific data, override the API definition
  const definition: ApiFormFieldType = useMemo(() => {
    let def = definitions.find((def) => def.name == field.name) || field;

    def = {
      ...def,
      ...field
    };

    // Format the errors
    if (def.errors?.length == 1) {
      def.error = def.errors[0];
    }

    return def;
  }, [field, definitions]);

  switch (definition.type) {
    case 'url':
    case 'string':
      return <TextInput {...definition} />;
    default:
      return (
        <Alert color="red" title="Error">
          Unknown field type for field '{definition.name}': {definition.type}
        </Alert>
      );
  }
}

/**
 * An ApiForm component is a modal form which is rendered dynamically,
 * based on an API endpoint.
 * @param url : The API endpoint to fetch the form from.
 * @param fields : The fields to render in the form.
 * @param opened : Whether the form is opened or not.
 * @param onClose : A callback function to call when the form is closed.
 * @param onFormSuccess : A callback function to call when the form is submitted successfully.
 * @param onFormError : A callback function to call when the form is submitted with errors.
 */
export function ApiForm({
  name,
  url,
  pk,
  title,
  fields,
  opened,
  onClose,
  onFormSuccess,
  onFormError,
  cancelText = t`Cancel`,
  submitText = t`Submit`,
  method = 'PUT'
}: {
  name: string;
  url: string;
  pk?: number;
  title: string;
  fields: ApiFormFieldType[];
  cancelText?: string;
  submitText?: string;
  method?: string;
  opened: boolean;
  onClose?: () => void;
  onFormSuccess?: () => void;
  onFormError?: () => void;
}) {
  // Form state
  const form = useForm({});

  // Form field definitions (via API)
  const [fieldDefinitions, setFieldDefinitions] = useState<ApiFormFieldType[]>(
    []
  );

  // Error observed during form construction
  const [error, setError] = useState<string>('');

  const definitionQuery = useQuery({
    enabled: opened && !!url,
    queryKey: ['form-definition', name, url, pk, fields],
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
          console.error('Error fetching field definitions:', error);
          setError(error.message);
          setFieldDefinitions([]);
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
    let u = url;

    if (pk && pk > 0) {
      u += `${pk}/`;
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
    let actions = response.data?.actions[method.toUpperCase()] || [];

    if (actions.length == 0) {
      setError(`Permission denied for ${method} at ${url}`);
      return [];
    }

    let definitions: ApiFormFieldType[] = [];

    for (const fieldName in actions) {
      const field = actions[fieldName];
      definitions.push({
        name: fieldName,
        label: field.label,
        description: field.help_text,
        value: field.value,
        type: field.type,
        required: field.required,
        placeholder: field.placeholder,
        icon: field.icon
      });
    }

    return definitions;
  }

  return (
    <Modal
      size="xl"
      radius="sm"
      opened={opened}
      onClose={onClose}
      title={title}
    >
      <Stack>
        <Divider />
        {definitionQuery.isFetching && (
          <Center>
            <Loader />
          </Center>
        )}
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
        {canRender && (
          <ScrollArea>
            <Stack spacing="md">
              {fields.map((field) => (
                <ApiFormField
                  key={field.name}
                  field={field}
                  definitions={fieldDefinitions}
                />
              ))}
            </Stack>
          </ScrollArea>
        )}
        <Divider />
        <Group position="right">
          <Button onClick={onClose} variant="outline" radius="sm" color="red">
            {cancelText}
          </Button>
          <Button
            onClick={() => null}
            variant="outline"
            radius="sm"
            color="green"
            disabled={!canSubmit}
          >
            <Group position="right" spacing={5} noWrap={true}>
              <Loader size="xs" />
              {submitText}
            </Group>
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
