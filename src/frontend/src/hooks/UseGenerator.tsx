import { useDebouncedValue } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { api } from '../App';

export type GeneratorProps = {
  endpoint: ApiEndpoints;
  key: string;
  initialQuery?: Record<string, any>;
  onGenerate?: (value: any) => void;
};

export type GeneratorState = {
  query: Record<string, any>;
  result: any;
  update: (params: Record<string, any>, overwrite?: boolean) => void;
};

/* Hook for managing generation of data via the InvenTree API.
 * We pass an endpoint, and start with an initially empty query.
 * We can pass additional parameters to the query, and update the query as needed.
 * Each update calls a new query to the API, and the result is stored in the state.
 */
export function useGenerator(props: GeneratorProps): GeneratorState {
  // Track the result
  const [result, setResult] = useState<any>(null);

  // Track the generator query
  const [query, setQuery] = useState<Record<string, any>>({});

  // Prevent rapid updates
  const [debouncedQuery] = useDebouncedValue<Record<string, any>>(query, 100);

  // Callback to update the generator query
  const update = useCallback(
    (params: Record<string, any>, overwrite?: boolean) => {
      if (overwrite) {
        setQuery(params);
      } else {
        setQuery((query) => ({
          ...query,
          ...params
        }));
      }
    },
    []
  );

  // API query handler
  const queryGenerator = useQuery({
    enabled: true,
    queryKey: [
      'generator',
      props.key,
      props.endpoint,
      props.initialQuery,
      debouncedQuery
    ],
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    queryFn: async () => {
      const generatorQuery = {
        ...debouncedQuery,
        ...(props.initialQuery ?? {})
      };

      return api
        .post(apiUrl(props.endpoint), generatorQuery)
        .then((response) => {
          const value = response?.data[props.key];
          setResult(value);

          props.onGenerate?.(value);

          return response;
        })
        .catch((error) => {
          console.error(
            `Error generating ${props.key} @ ${props.endpoint}:`,
            error
          );
        });
    }
  });

  return {
    query,
    update,
    result
  };
}

// Generate a batch code with provided data
export function useBatchCodeGenerator({
  initialQuery,
  onGenerate
}: {
  initialQuery?: Record<string, any>;
  onGenerate?: (value: any) => void;
}): GeneratorState {
  return useGenerator({
    endpoint: ApiEndpoints.generate_batch_code,
    key: 'batch_code',
    initialQuery: initialQuery,
    onGenerate: onGenerate
  });
}

// Generate a serial number with provided data
export function useSerialNumberGenerator({
  initialQuery,
  onGenerate
}: {
  initialQuery?: Record<string, any>;
  onGenerate?: (value: any) => void;
}): GeneratorState {
  return useGenerator({
    endpoint: ApiEndpoints.generate_serial_number,
    key: 'serial_number',
    initialQuery: initialQuery,
    onGenerate: onGenerate
  });
}
