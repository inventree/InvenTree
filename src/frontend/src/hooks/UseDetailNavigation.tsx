import { resolveItem } from '@lib/functions/Conversion';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { useApi } from '../contexts/ApiContext';
import {
  buildDetailNavigationTarget,
  type DetailNavigationTarget,
  readDetailNavigationContext
} from '../functions/DetailNavigation';

export function useDetailNavigation(): {
  previous?: DetailNavigationTarget;
  next?: DetailNavigationTarget;
} {
  const api = useApi();
  const location = useLocation();
  const context = useMemo(
    () => readDetailNavigationContext(location.search),
    [location.search]
  );

  const listQuery = useQuery({
    enabled: context !== undefined,
    queryKey: [
      'detail-navigation',
      context?.apiUrl,
      context?.query.toString(),
      context?.index,
      context?.pk,
      context?.field
    ],
    queryFn: async () => {
      if (!context) {
        return [];
      }

      const params = new URLSearchParams(context.query);
      params.set('limit', '3');
      params.set('offset', String(Math.max(context.index - 1, 0)));

      const response = await api.get(context.apiUrl, {
        params,
        timeout: 10000
      });
      const records = response.data?.results ?? response.data ?? [];

      return Array.isArray(records) ? records : [];
    }
  });

  if (!context) {
    return {};
  }

  const records = listQuery.data ?? [];
  const currentRecordIndex = records.findIndex(
    (record: any) => String(resolveItem(record, context.field)) === context.pk
  );
  const listOffset = Math.max(context.index - 1, 0);

  const createTarget = (
    record: any,
    relativeIndex: number
  ): DetailNavigationTarget | undefined => {
    const targetPk = resolveItem(record, context.field);

    if (targetPk === null || targetPk === undefined) {
      return undefined;
    }

    return buildDetailNavigationTarget(
      location.pathname,
      location.search,
      context,
      targetPk,
      listOffset + relativeIndex
    );
  };

  if (currentRecordIndex < 0) {
    return {};
  }

  return {
    previous:
      currentRecordIndex > 0
        ? createTarget(records[currentRecordIndex - 1], currentRecordIndex - 1)
        : undefined,
    next:
      currentRecordIndex < records.length - 1
        ? createTarget(records[currentRecordIndex + 1], currentRecordIndex + 1)
        : undefined
  };
}
