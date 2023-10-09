import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo, useState } from 'react';

import { api } from '../App';

export type InstanceQueryProps = {
  url: string;
  pk: string | undefined;
  params?: any;
  default: any;
};

/**
 * Custom hook for loading a single endpoint from the API
 *
 * - Queries the API for a single instance of an object, and returns the result.
 * - Provides a callback function to refresh the instance
 *
 * To use this hook:
 * const { instance, refreshInstance } = useInstance(url: string, pk: number)
 */
export function useInstance({
  url,
  pk,
  params = {},
  defaultValue = {},
  fetchOnMount = false,
  hasPrimaryKey = true
}: {
  url: string;
  pk?: string;
  params?: any;
  hasPrimaryKey?: boolean;
  defaultValue?: any;
  fetchOnMount?: boolean;
}) {
  const [instance, setInstance] = useState<any>(defaultValue);

  const queryUrl = useMemo(() => {
    let _url = url;

    if (!_url.endsWith('/')) {
      _url += '/';
    }

    if (hasPrimaryKey && pk) {
      _url += pk + '/';
    }

    return _url;
  }, [url, pk]);

  const instanceQuery = useQuery({
    queryKey: ['instance', url, pk, params],
    queryFn: async () => {
      if (hasPrimaryKey) {
        if (pk == null || pk == undefined || pk.length == 0) {
          setInstance(defaultValue);
          return null;
        }
      }

      return api
        .get(queryUrl, {
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
          console.error(`Error fetching instance ${url}${pk}:`, error);
          return null;
        });
    },
    refetchOnMount: fetchOnMount,
    refetchOnWindowFocus: false
  });

  const refreshInstance = useCallback(function () {
    instanceQuery.refetch();
  }, []);

  return { instance, refreshInstance, instanceQuery };
}
