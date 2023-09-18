import { useQuery } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import { api } from '../App';

/**
 * Custom hook for loading a single instance of an instance from the API
 *
 * - Queries the API for a single instance of an object, and returns the result.
 * - Provides a callback function to refresh the instance
 *
 * To use this hook:
 * const { instance, refreshInstance } = useInstance(url: string, pk: number)
 */
export function useInstance(url: string, pk: string | undefined) {
  const [instance, setInstance] = useState<any>({});

  const instanceQuery = useQuery({
    queryKey: ['instance', url, pk],
    enabled: pk != null && pk != undefined && pk.length > 0,
    queryFn: async () => {
      return api
        .get(url + pk + '/')
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
          console.error(`Error fetching instance ${url}${pk}:`, error);
          return null;
        });
    },
    refetchOnMount: false,
    refetchOnWindowFocus: false
  });

  const refreshInstance = useCallback(
    function () {
      instanceQuery.refetch();
    },
    [instanceQuery]
  );

  return { instance, refreshInstance, instanceQuery };
}
