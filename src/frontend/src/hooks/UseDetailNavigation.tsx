import { resolveItem } from '@lib/functions/Conversion';
import { navigateToLink } from '@lib/functions/Navigation';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useApi } from '../contexts/ApiContext';
import {
  type DetailNavigationAction,
  buildDetailNavigationTarget,
  readDetailNavigationContext
} from '../functions/DetailNavigation';

type DetailNavigationData = {
  records: any[];
  total: number;
};

export type DetailNavigationState = {
  previous?: DetailNavigationAction;
  next?: DetailNavigationAction;
  position?: {
    current: number;
    total: number;
  };
  isLoading: boolean;
};

export function useDetailNavigation(): DetailNavigationState {
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
    queryFn: async (): Promise<DetailNavigationData> => {
      if (!context) {
        return { records: [], total: 0 };
      }

      const params = new URLSearchParams(context.query);
      const offset = Math.max(context.index - 1, 0);

      params.set('limit', '3');
      params.set('offset', String(offset));

      const response = await api.get(context.apiUrl, {
        params,
        timeout: 10000
      });

      const rawRecords = response.data?.results ?? response.data ?? [];
      const records = Array.isArray(rawRecords) ? rawRecords : [];
      const count = Number(response.data?.count);

      return {
        records,
        total: Number.isFinite(count) && count >= 0 ? count : records.length
      };
    }
  });

  const records = listQuery.data?.records ?? [];
  const total = listQuery.data?.total ?? 0;
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
      onClick: (event) => navigateToLink(href, navigate, event)
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
    position:
      total > context.index
        ? {
            current: context.index + 1,
            total
          }
        : undefined,
    isLoading: listQuery.isLoading
  };
}
