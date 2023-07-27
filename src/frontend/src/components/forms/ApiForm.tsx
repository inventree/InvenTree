import { Modal } from '@mantine/core';
import { Center, Loader, Stack, Text } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useQuery } from '@tanstack/react-query';
import { AxiosResponse } from 'axios';
import { useEffect } from 'react';
import { useState } from 'react';
import { useMemo } from 'react';

import { api } from '../../App';

/* Definition of the ApiForm field component.
 * - The 'name' attribute *must* be provided
 * - All other attributes are optional, and may be provided by the API
 * - However, they can be overridden by the user
 */
export type ApiFormField = {
  name: string;
  label?: string;
  value?: any;
  type?: string;
  required?: boolean;
  placeholder?: string;
  help_text?: string;
  icon?: string;
  errors?: string[];
};

/**
 * Extract a list of field definitions from an API response.
 * @param response : The API response to extract the field definitions from.
 * @returns A list of field definitions.
 */
function extractFieldDefinitions(response: AxiosResponse): ApiFormField[] {
  // TODO: [];
  return [];
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
  onFormError
}: {
  name: string;
  url: string;
  pk?: number;
  title: string;
  fields: ApiFormField[];
  opened: boolean;
  onClose?: () => void;
  onFormSuccess?: () => void;
  onFormError?: () => void;
}) {
  // Form state
  const form = useForm({});

  // Form field definitions (via API)
  const [fieldDefinitions, setFieldDefinitions] = useState<ApiFormField[]>([]);

  const fetchFieldDefinitions = async () => {};

  const definitionQuery = useQuery({
    enabled: opened && !!url,
    queryKey: ['form-definition', name, url, pk, fields],
    queryFn: async () => {
      let _url = url;

      if (pk && pk > 0) {
        _url += `${pk}/`;
      }
      console.log('Fetching form definition from API:', _url);

      return api
        .options(_url)
        .then((response) => {
          console.log('response:', response);
          setFieldDefinitions(extractFieldDefinitions(response));
          return response;
        })
        .catch((error) => {
          console.error('error:', error);
          setFieldDefinitions([]);
        });
    }
  });

  return (
    <Modal opened={opened} onClose={onClose} title={title}>
      <Stack>
        <Center>
          {definitionQuery.isFetching && <Loader />}
          Hello world
          {definitionQuery.isSuccess && <Text>Success!</Text>}
          {definitionQuery.isError && <Text>Error!</Text>}
          {definitionQuery.isLoading && <Text>Loading...</Text>}
        </Center>
      </Stack>
    </Modal>
  );
}
