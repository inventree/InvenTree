import { t } from '@lingui/macro';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { api } from '../App';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from '../states/ApiState';

/**
 * Hook for generating a placeholder text for a serial number input
 *
 * This hook fetches the latest serial number information for a given part and generates a placeholder string.
 *
 * @param partId The ID of the part to fetch serial number information for
 * @param key A unique key to identify the query
 * @param enabled Whether the query should be enabled
 */
export function useSerialNumberPlaceholder({
  partId,
  key,
  enabled = true
}: {
  partId: number;
  key: string;
  enabled?: boolean;
}): string | undefined {
  // Fetch serial number information (if available)
  const snQuery = useQuery({
    queryKey: ['serial-placeholder', key, partId],
    enabled: enabled ?? true,
    queryFn: async () => {
      if (!partId) {
        return null;
      }

      const url = apiUrl(ApiEndpoints.part_serial_numbers, partId);

      return api
        .get(url)
        .then((response) => {
          if (response.status === 200) {
            return response.data;
          } else {
            return null;
          }
        })
        .catch(() => {
          return null;
        });
    }
  });

  const placeholder = useMemo(() => {
    if (!enabled) {
      return undefined;
    } else if (snQuery.data?.next) {
      return `${t`Next serial number`}: ${snQuery.data.next}`;
    } else if (snQuery.data?.latest) {
      return `${t`Latest serial number`}: ${snQuery.data.latest}`;
    } else {
      return undefined;
    }
  }, [enabled, snQuery.data]);

  return placeholder;
}
