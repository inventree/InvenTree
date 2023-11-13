import { useQuery } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import { api } from '../App';
import { ApiPaths } from '../enums/ApiEndpoints';
import { apiUrl } from '../states/ApiState';

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
  params = {},
  defaultValue = {},
  hasPrimaryKey = true,
  refetchOnMount = true,
  refetchOnWindowFocus = false
}: {
  endpoint: ApiPaths;
  pk?: string | undefined;
  hasPrimaryKey?: boolean;
  params?: any;
  defaultValue?: any;
  refetchOnMount?: boolean;
  refetchOnWindowFocus?: boolean;
}) {
  const [instance, setInstance] = useState<any>(defaultValue);

  const instanceQuery = useQuery({
    queryKey: ['instance', endpoint, pk, params],
    queryFn: async () => {
      if (hasPrimaryKey) {
        if (pk == null || pk == undefined || pk.length == 0 || pk == '-1') {
          setInstance(defaultValue);
          return null;
        }
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
              setInstance(defaultValue);
              return null;
          }
        })
        .catch((error) => {
          setInstance(defaultValue);
          console.error(`Error fetching instance ${url}:`, error);
          return null;
        });
    },
    refetchOnMount: refetchOnMount,
    refetchOnWindowFocus: refetchOnWindowFocus
  });

  const refreshInstance = useCallback(function () {
    instanceQuery.refetch();
  }, []);

  return { instance, refreshInstance, instanceQuery };
}
