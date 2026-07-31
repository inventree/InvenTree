import { apiUrl } from '@lib/functions/Api';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { useApi } from '../contexts/ApiContext';

export const NAV_PARAM_PREFIX = '_nav_';

export interface NavContext {
  endpoint: string;
  filters: Record<string, string>;
  ordering: string;
}

export function encodeNavContext(ctx: NavContext): Record<string, string> {
  const out: Record<string, string> = {
    [`${NAV_PARAM_PREFIX}endpoint`]: ctx.endpoint,
    [`${NAV_PARAM_PREFIX}ordering`]: ctx.ordering
  };
  for (const [k, v] of Object.entries(ctx.filters)) {
    out[`${NAV_PARAM_PREFIX}f_${k}`] = v;
  }
  return out;
}

function decodeNavContext(params: URLSearchParams): NavContext | null {
  const endpoint = params.get(`${NAV_PARAM_PREFIX}endpoint`);
  const ordering = params.get(`${NAV_PARAM_PREFIX}ordering`) ?? 'pk';

  if (!endpoint) return null;

  const filters: Record<string, string> = {};
  for (const [k, v] of params.entries()) {
    if (
      k.startsWith(`${NAV_PARAM_PREFIX}f_`) &&
      v !== 'undefined' &&
      v !== 'null' &&
      v !== ''
    ) {
      filters[k.slice(`${NAV_PARAM_PREFIX}f_`.length)] = v;
    }
  }

  return { endpoint, filters, ordering };
}

interface UseNextPrevSiblingsResult {
  prevPk?: number;
  nextPk?: number;
  isLoading: boolean;
  navParams: Record<string, string>;
}

export function useNextPrevSiblings(
  currentPk: number | undefined
): UseNextPrevSiblingsResult {
  const api = useApi();
  const [searchParams] = useSearchParams();
  const ctx = decodeNavContext(searchParams);

  const navParams: Record<string, string> = {};
  if (ctx) {
    for (const [k, v] of searchParams.entries()) {
      if (k.startsWith(NAV_PARAM_PREFIX)) {
        navParams[k] = v;
      }
    }
  }

  const enabled = !!currentPk && !!ctx;

  const { data: prevPk, isLoading: prevLoading } = useQuery({
    queryKey: [
      'next-prev',
      ctx?.endpoint,
      currentPk,
      'prev',
      ctx?.filters,
      ctx?.ordering
    ],
    queryFn: async () => {
      const response = await api.get(apiUrl(ctx!.endpoint), {
        params: {
          ...ctx!.filters,
          pk_lt: currentPk,
          ordering: `-${ctx!.ordering.replace(/^-/, '')}`,
          limit: 1
        }
      });
      return response.data?.results?.[0]?.pk as number | undefined;
    },
    enabled
  });

  const { data: nextPk, isLoading: nextLoading } = useQuery({
    queryKey: [
      'next-prev',
      ctx?.endpoint,
      currentPk,
      'next',
      ctx?.filters,
      ctx?.ordering
    ],
    queryFn: async () => {
      const response = await api.get(apiUrl(ctx!.endpoint), {
        params: {
          ...ctx!.filters,
          pk_gt: currentPk,
          ordering: ctx!.ordering,
          limit: 1
        }
      });
      return response.data?.results?.[0]?.pk as number | undefined;
    },
    enabled
  });

  return {
    prevPk,
    nextPk,
    isLoading: prevLoading || nextLoading,
    navParams
  };
}
