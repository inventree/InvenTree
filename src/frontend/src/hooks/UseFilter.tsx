/*
 * Custom hook for retrieving a list of items from the API,
 * and turning them into "filters" for use in the frontend table framework.
 */
import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';

import type { TableFilterChoice } from '@lib/types/Filters';
import { useApi } from '../contexts/ApiContext';
import { resolveItem } from '../functions/conversion';

type UseFilterProps = {
  url: string;
  method?: 'GET' | 'POST' | 'OPTIONS';
  params?: any;
  accessor?: string;
  transform: (item: any) => TableFilterChoice;
};

export function useFilters(props: UseFilterProps) {
  const api = useApi();

  const query = useQuery({
    enabled: true,
    gcTime: 500,
    queryKey: [props.url, props.method, props.params],
    queryFn: async () => {
      return await api
        .request({
          url: props.url,
          method: props.method ?? 'GET',
          params: props.params
        })
        .then((response) => {
          const data = resolveItem(response, props.accessor ?? 'data');

          if (data == null || data == undefined) {
            return [];
          }

          return data;
        });
    }
  });

  const choices: TableFilterChoice[] = useMemo(() => {
    const opts = query.data?.map(props.transform) ?? [];

    // Ensure stringiness
    return opts.map((opt: any) => {
      return {
        value: opt.value.toString(),
        label: opt?.label?.toString() ?? opt.value.toString()
      };
    });
  }, [props.transform, query.data]);

  const refresh = useCallback(() => {
    query.refetch();
  }, []);

  return {
    choices,
    refresh
  };
}
