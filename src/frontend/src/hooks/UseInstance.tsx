import { useQuery } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import { api } from '../App';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { PathParams, apiUrl } from '../states/ApiState';

/**
 * Custom hook for loading a single instance of an instance from the API
 *
 * - Queries the API for a single instance of an object, and returns the result.
 * - Provides a callback function to refresh the instance
 *
 * To use this hook:
 * const { instance, refreshInstance } = useInstance(url: string, pk: number)
 */
export function useInstance<T = any>({
  endpoint,
  pk,
  params = {},
  defaultValue = {},
  pathParams,
  hasPrimaryKey = true,
  refetchOnMount = true,
  refetchOnWindowFocus = false,
  throwError = false
}: {
  endpoint: ApiEndpoints;
  pk?: string | undefined;
  hasPrimaryKey?: boolean;
  params?: any;
  pathParams?: PathParams;
  defaultValue?: any;
  refetchOnMount?: boolean;
  refetchOnWindowFocus?: boolean;
  throwError?: boolean;
}) {
  const [instance, setInstance] = useState<T | undefined>(defaultValue);

  const instanceQuery = useQuery<T>({
    queryKey: ['instance', endpoint, pk, params],
    queryFn: async () => {
      if (hasPrimaryKey) {
        if (pk == null || pk == undefined || pk.length == 0 || pk == '-1') {
          setInstance(defaultValue);
          return null;
        }
      }

      const url = apiUrl(endpoint, pk, pathParams);

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

          if (throwError) throw error;

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
