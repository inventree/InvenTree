import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo, useState } from 'react';

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
  throwError = false,
  updateInterval
}: {
  endpoint: ApiEndpoints;
  pk?: string | number | undefined;
  hasPrimaryKey?: boolean;
  params?: any;
  pathParams?: PathParams;
  defaultValue?: any;
  refetchOnMount?: boolean;
  refetchOnWindowFocus?: boolean;
  throwError?: boolean;
  updateInterval?: number;
}) {
  const [instance, setInstance] = useState<T | undefined>(defaultValue);

  const [requestStatus, setRequestStatus] = useState<number>(0);

  const instanceQuery = useQuery<T>({
    queryKey: ['instance', endpoint, pk, params, pathParams],
    queryFn: async () => {
      if (hasPrimaryKey) {
        if (
          pk == null ||
          pk == undefined ||
          pk.toString().length == 0 ||
          pk == '-1'
        ) {
          setInstance(defaultValue);
          return defaultValue;
        }
      }

      const url = apiUrl(endpoint, pk, pathParams);

      return api
        .get(url, {
          timeout: 10000,
          params: params
        })
        .then((response) => {
          setRequestStatus(response.status);
          switch (response.status) {
            case 200:
              setInstance(response.data);
              return response.data;
            default:
              setInstance(defaultValue);
              return defaultValue;
          }
        })
        .catch((error) => {
          setRequestStatus(error.response?.status || 0);
          setInstance(defaultValue);
          console.error(`ERR: Error fetching instance ${url}:`, error);

          if (throwError) throw error;

          return defaultValue;
        });
    },
    refetchOnMount: refetchOnMount,
    refetchOnWindowFocus: refetchOnWindowFocus,
    refetchInterval: updateInterval
  });

  const refreshInstance = useCallback(function () {
    instanceQuery.refetch();
  }, []);

  return { instance, refreshInstance, instanceQuery, requestStatus };
}
