import { useQuery } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import { api } from '../App';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from '../states/ApiState';

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
export function useGenerator(
  endpoint: ApiEndpoints,
  key: string,
  onGenerate?: (value: any) => void
): GeneratorState {
  // Track the result
  const [result, setResult] = useState<any>(null);

  // Track the generator query
  const [query, setQuery] = useState<Record<string, any>>({});

  // Callback to update the generator query
  const update = useCallback(
    (params: Record<string, any>, overwrite?: boolean) => {
      if (overwrite ?? false) {
        setQuery(params);
      } else {
        setQuery({
          ...query,
          ...params
        });
      }

      queryGenerator.refetch();
    },
    [query]
  );

  // API query handler
  const queryGenerator = useQuery({
    enabled: true,
    queryKey: ['generator', key, endpoint, query],
    queryFn: async () => {
      return api.post(apiUrl(endpoint), query).then((response) => {
        const value = response?.data[key];
        setResult(value);

        if (onGenerate) {
          onGenerate(value);
        }

        return response;
      });
    }
  });

  return {
    query,
    update,
    result
  };
}
