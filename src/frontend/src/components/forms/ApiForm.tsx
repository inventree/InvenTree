import { t } from '@lingui/macro';
import {
  Alert,
  Checkbox,
  Divider,
  LoadingOverlay,
  Modal,
  NumberInput,
  ScrollArea,
  Select,
  TextInput
} from '@mantine/core';
import { Button, Center, Group, Loader, Stack, Text } from '@mantine/core';
import { DateInput } from '@mantine/dates';
import { UseFormReturnType, useForm } from '@mantine/form';
import { useDebouncedValue } from '@mantine/hooks';
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
  default?: any;
  icon?: ReactNode;
  fieldType?: string;
  api_url?: string;
  model?: string;
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

  // Change value to a date object if required
  switch (def.fieldType) {
    case 'date':
      if (def.value) {
        def.value = new Date(def.value);
      }
      break;
    default:
      break;
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

  const [value, setValue] = useState<string>('');
  const [searchText] = useDebouncedValue(value, 500);

  const selectQuery = useQuery({
    enabled: !definition.disabled && !!definition.api_url && !definition.hidden,
    queryKey: [`related-field-${definition.name}`, searchText],
    queryFn: async () => {
      console.log('Searching for', searchText);
    }
  });

  function onSearchChange(value: string) {
    console.log('Search change:', value, definition.api_url, definition.model);
    setValue(value);
  }

  return (
    <Select
      withinPortal={true}
      searchable={true}
      onSearchChange={onSearchChange}
      data={[]}
      clearable={!definition.required}
      {...definition}
    />
  );
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
      return (
        <TextInput
          {...definition}
          type="url"
          onChange={(event) => onChange(event.currentTarget.value)}
        />
      );
    case 'email':
      return (
        <TextInput
          {...definition}
          type="email"
          onChange={(event) => onChange(event.currentTarget.value)}
        />
      );
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
    case 'date':
      return (
        <DateInput
          radius="sm"
          {...definition}
          clearable={!definition.required}
          onChange={(value) => onChange(value)}
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
          Unknown field type for field '{definition.name}': '
          {definition.fieldType}'
        </Alert>
      );
  }
}

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
