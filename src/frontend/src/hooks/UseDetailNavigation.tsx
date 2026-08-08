import { resolveItem } from '@lib/functions/Conversion';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useApi } from '../contexts/ApiContext';
import {
  buildDetailNavigationTarget,
  type DetailNavigationAction,
  readDetailNavigationContext
} from '../functions/DetailNavigation';

export function useDetailNavigation(): {
  previous?: DetailNavigationAction;
  next?: DetailNavigationAction;
  isLoading: boolean;
} {
  const api = useApi();
  const location = useLocation();
  const navigate = useNavigate();

  const context = useMemo(
    () => readDetailNavigationContext(location.search),
    [location.search]
  );

  const listQuery = useQuery({
    enabled: context !== null,
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
      const offset = Math.max(context.index - 1, 0);

      params.set('limit', '3');
      params.set('offset', String(offset));

      const response = await api.get(context.apiUrl, {
        params,
        timeout: 10000
      });

      const records = response.data?.results ?? response.data ?? [];
      return Array.isArray(records) ? records : [];
    }
  });

  const records = listQuery.data ?? [];
  const currentRecordIndex = context
    ? records.findIndex(
        (record: any) =>
          String(resolveItem(record, context.field)) === context.pk
      )
    : -1;
  const listOffset = context ? Math.max(context.index - 1, 0) : 0;

  const createAction = (
    record: any,
    relativeIndex: number
  ): DetailNavigationAction | undefined => {
    if (!context) {
      return undefined;
    }

    const targetPk = resolveItem(record, context.field);
    if (targetPk === null || targetPk === undefined) {
      return undefined;
    }

    const targetIndex = listOffset + relativeIndex;
    const href = buildDetailNavigationTarget(
      location.pathname,
      location.search,
      context,
      targetPk,
      targetIndex
    );

    return {
      href,
      onClick: (event) => {
        if (
          event.defaultPrevented ||
          event.button !== 0 ||
          event.ctrlKey ||
          event.metaKey ||
          event.shiftKey
        ) {
          return;
        }

        event.preventDefault();
        navigate(href);
      }
    };
  };

  if (!context || currentRecordIndex < 0) {
    return { isLoading: listQuery.isLoading };
  }

  return {
    previous:
      currentRecordIndex > 0
        ? createAction(records[currentRecordIndex - 1], currentRecordIndex - 1)
        : undefined,
    next:
      currentRecordIndex < records.length - 1
        ? createAction(records[currentRecordIndex + 1], currentRecordIndex + 1)
        : undefined,
    isLoading: listQuery.isLoading
  };
}
