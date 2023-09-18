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
export function useInstance(url: string, pk: number | null) {
  const [instance, setInstance] = useState<any>(null);

  const refreshInstance = useCallback(
    function () {
      if (pk == null || pk <= 0) {
        setInstance({});
      } else {
        api
          .get(url + pk + '/')
          .then((response) => {
            switch (response.status) {
              case 200:
                setInstance(response.data);
                break;
              default:
                setInstance({});
                break;
            }
          })
          .catch((error) => {
            console.error(`Error fetching instance ${url}${pk}:`, error);
            setInstance({});
          });
      }
    },
    [url, pk]
  );

  return { instance, refreshInstance };
}
