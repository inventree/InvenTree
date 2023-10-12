import { useQuery } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import { api } from '../App';
import { ApiPaths, apiUrl } from '../states/ApiState';

/**
 * Custom hook for loading a single instance of an instance from the API
 *
 * - Queries the API for a single instance of an object, and returns the result.
 * - Provides a callback function to refresh the instance
 *
 * To use this hook:
 * const { instance, refreshInstance } = useInstance(url: string, pk: number)
 */
export function useInstance({
  endpoint,
  pk,
  params = {}
}: {
  endpoint: ApiPaths;
  pk: string | undefined;
  params?: any;
}) {
  const [instance, setInstance] = useState<any>({});

  const instanceQuery = useQuery({
    queryKey: ['instance', endpoint, pk, params],
    queryFn: async () => {
      if (pk == null || pk == undefined || pk.length == 0) {
        setInstance({});
        return null;
      }

      let url = apiUrl(endpoint, pk);

      return api
        .get(url, {
          params: params
        })
        .then((response) => {
          switch (response.status) {
            case 200:
              setInstance(response.data);
              return response.data;
            default:
              setInstance({});
              return null;
          }
        })
        .catch((error) => {
          setInstance({});
          console.error(`Error fetching instance ${url}:`, error);
          return null;
        });
    },
    refetchOnMount: false,
    refetchOnWindowFocus: false
  });

  const refreshInstance = useCallback(function () {
    instanceQuery.refetch();
  }, []);

  return { instance, refreshInstance, instanceQuery };
}
