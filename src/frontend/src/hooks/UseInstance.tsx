import {
  type QueryObserverResult,
  type UseQueryResult,
  useQuery
} from '@tanstack/react-query';
import { useCallback, useMemo, useState } from 'react';

import type { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { PathParams } from '@lib/types/Core';
import { useApi } from '../contexts/ApiContext';

export interface UseInstanceResult {
  instance: any;
  setInstance: (instance: any) => void;
  refreshInstance: () => void;
  refreshInstancePromise: () => Promise<QueryObserverResult<any, any>>;
  instanceQuery: UseQueryResult;
  isLoaded: boolean;
}

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
  disabled,
  hasPrimaryKey = true,
  refetchOnMount = true,
  refetchOnWindowFocus = false,
  updateInterval
}: {
  endpoint: ApiEndpoints;
  pk?: string | number | undefined;
  hasPrimaryKey?: boolean;
  params?: any;
  pathParams?: PathParams;
  disabled?: boolean;
  defaultValue?: any;
  refetchOnMount?: boolean;
  refetchOnWindowFocus?: boolean;
  updateInterval?: number;
}): UseInstanceResult {
  const api = useApi();

  const [instance, setInstance] = useState<T | undefined>(defaultValue);

  const instanceQuery = useQuery<T>({
    enabled: !disabled,
    queryKey: [
      'instance',
      endpoint,
      pk,
      JSON.stringify(params),
      JSON.stringify(pathParams),
      disabled
    ],
    retry: (failureCount, error: any) => {
      // If it's a 404, don't retry
      if (error.response?.status == 404) {
        return false;
      }

      // Otherwise, retry up to 3 times
      return failureCount < 3;
    },
    queryFn: async () => {
      if (disabled) {
        return defaultValue;
      }

      if (hasPrimaryKey) {
        if (
          pk == null ||
          pk == undefined ||
          pk.toString().length == 0 ||
          pk.toString() == '-1'
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
          switch (response.status) {
            case 200:
              setInstance(response.data);
              return response.data;
            default:
              setInstance(defaultValue);
              return defaultValue;
          }
        });
    },
    refetchOnMount: refetchOnMount,
    refetchOnWindowFocus: refetchOnWindowFocus ?? false,
    refetchInterval: updateInterval
  });

  const isLoaded = useMemo(() => {
    return (
      instanceQuery.isFetched &&
      instanceQuery.isSuccess &&
      !instanceQuery.isError
    );
  }, [instanceQuery]);

  const refreshInstance = useCallback(() => {
    instanceQuery.refetch();
  }, []);

  const refreshInstancePromise = useCallback(() => {
    return instanceQuery.refetch();
  }, []);

  return {
    instance,
    setInstance,
    refreshInstance,
    refreshInstancePromise,
    instanceQuery,
    isLoaded
  };
}
