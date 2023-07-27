import { t } from '@lingui/macro';
import {
  Alert,
  Checkbox,
  Divider,
  Modal,
  NumberInput,
  ScrollArea,
  Select,
  TextInput
} from '@mantine/core';
import { Button, Center, Group, Loader, Stack, Text } from '@mantine/core';
import { UseFormReturnType, useForm } from '@mantine/form';
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
  fieldType?: string;
  required?: boolean;
  hidden?: boolean;
  disabled?: boolean;
  placeholder?: string;
  description?: string;
  errors?: string[];
  error?: any;
};

/*
 * Build a complete field definition based on the provided data
 */
function constructField({
  form,
  field,
  definitions
}: {
  form: UseFormReturnType<Record<string, unknown>>;
  field: ApiFormFieldType;
  definitions: ApiFormFieldType[];
}) {
  let def = definitions.find((def) => def.name == field.name) || field;

  def = {
    ...def,
    ...field
  };

  // Format the errors
  if (def.errors?.length == 1) {
    def.error = def.errors[0];
  } else if (def.errors?.length ?? 0 > 1) {
    // TODO: Build a custom error stack?
  } else {
    def.error = null;
  }

  // Retrieve the latest value from the form
  let value = form.values[def.name];

  if (value != undefined) {
    def.value = value;
  }

  return def;
}

/**
 * Render a 'select' field for searching the database against a particular model type
 */
function RelatedModelField({
  form,
  field,
  definitions
}: {
  form: UseFormReturnType<Record<string, unknown>>;
  field: ApiFormFieldType;
  definitions: ApiFormFieldType[];
}) {
  // Extract field definition from provided data
  // Where user has provided specific data, override the API definition
  const definition: ApiFormFieldType = useMemo(
    () =>
      constructField({
        form: form,
        field: field,
        definitions: definitions
      }),
    [form.values, field, definitions]
  );

  return <Select withinPortal={true} {...definition} data={[]} />;
}

/**
 * Render an individual form field
 */
function ApiFormField({
  form,
  field,
  definitions,
  onValueChange
}: {
  form: UseFormReturnType<Record<string, unknown>>;
  field: ApiFormFieldType;
  definitions: ApiFormFieldType[];
  onValueChange: (fieldName: string, value: any) => void;
}) {
  // Extract field definition from provided data
  // Where user has provided specific data, override the API definition
  const definition: ApiFormFieldType = useMemo(
    () =>
      constructField({
        form: form,
        field: field,
        definitions: definitions
      }),
    [form.values, field, definitions]
  );

  // Callback helper when form value changes
  function onChange(value: any) {
    // onValueChange(definition.name, value);
    form.setValues({ [definition.name]: value });
  }

  switch (definition.fieldType) {
    case 'related field':
      return (
        <RelatedModelField
          form={form}
          field={definition}
          definitions={definitions}
        />
      );
    case 'url':
    case 'string':
      return (
        <TextInput
          {...definition}
          onChange={(event) => onChange(event.currentTarget.value)}
        />
      );
    case 'boolean':
      return (
        <Checkbox
          radius="sm"
          {...definition}
          onChange={(event) => onChange(event.currentTarget.checked)}
        />
      );
    case 'integer':
    case 'decimal':
    case 'float':
    case 'number':
      return (
        <NumberInput
          radius="sm"
          {...definition}
          onChange={(value: number) => onChange(value)}
        />
      );
    default:
      return (
        <Alert color="red" title="Error">
          Unknown field type for field '{definition.name}':{' '}
          {definition.fieldType}
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
  method = 'PUT',
  fetchInitialData = false
}: {
  name: string;
  url: string;
  pk?: number;
  title: string;
  fields: ApiFormFieldType[];
  cancelText?: string;
  submitText?: string;
  fetchInitialData?: boolean;
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

  // Query manager for retrieving form definition from the server
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
          setError(error.message);
          setFieldDefinitions([]);
        });
    }
  });

  // Query manager for retrieiving initial data from the server
  const initialDataQuery = useQuery({
    enabled: fetchInitialData && opened && !!url && fieldDefinitions.length > 0,
    queryKey: ['form-initial-data', name, url, pk, fields, fieldDefinitions],
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
        fieldType: field.type,
        required: field.required,
        placeholder: field.placeholder
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
