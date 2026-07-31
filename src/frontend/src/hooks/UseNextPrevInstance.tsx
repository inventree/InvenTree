import { apiUrl } from '@lib/functions/Api';
import { useCallback, useMemo } from 'react';
import { useApi } from '../contexts/ApiContext';
import { useLocalLibState } from '../states/LocalLibState';

/**
 * Hook for resolving the previous/next sibling instance for a detail page.
 *
 * If a matching list-navigation context was captured when the user clicked
 * into this record (see InvenTreeTable row click / useLocalLibState.setListNavContext),
 * prev/next are resolved as O(1) lookups into that exact filtered/ordered list.
 *
 * Falls back to an ordering-aware pk__gt/pk__lt API query when no context is
 * available (direct link, bookmark, or standalone plugin usage).
 *
 * If a resolved neighbor pk no longer exists (404), it is dropped from the
 * stored context and the next available neighbor is fetched instead.
 */
export function useNextPrevInstance({
  endpoint,
  pk,
  ordering
}: {
  endpoint: string;
  pk?: string | number;
  ordering?: string;
}) {
  const api = useApi();

  const ctx = useLocalLibState((s) => s.listNavContexts[endpoint]);
  const dropPk = useLocalLibState((s) => s.dropListNavPk);

  const pkNum = pk != null ? Number(pk) : undefined;

  const fromContext = useMemo(() => {
    if (!ctx || pkNum == null) return null;
    const idx = ctx.pks.indexOf(pkNum);
    if (idx === -1) return null;
    return {
      prevPk: idx > 0 ? ctx.pks[idx - 1] : undefined,
      nextPk: idx < ctx.pks.length - 1 ? ctx.pks[idx + 1] : undefined
    };
  }, [ctx, pkNum]);

  const fetchNeighbor = useCallback(
    async (direction: 'prev' | 'next'): Promise<number | undefined> => {
      const filter =
        direction === 'prev' ? { pk__lt: pkNum } : { pk__gt: pkNum };
      const order =
        direction === 'prev' ? `-${ordering ?? 'pk'}` : (ordering ?? 'pk');
      const res = await api.get(apiUrl(endpoint), {
        params: { ...filter, ordering: order, limit: 1 }
      });
      return res.data?.results?.[0]?.pk;
    },
    [api, endpoint, pkNum, ordering]
  );

  const goTo = useCallback(
    async (direction: 'prev' | 'next'): Promise<number | undefined> => {
      const candidate = fromContext
        ? direction === 'prev'
          ? fromContext.prevPk
          : fromContext.nextPk
        : await fetchNeighbor(direction);

      if (candidate == null) return undefined;

      try {
        await api.get(apiUrl(endpoint, candidate));
        return candidate;
      } catch {
        // Stale reference (deleted / filtered out since context was captured)
        if (fromContext) dropPk(endpoint, candidate);
        return fetchNeighbor(direction);
      }
    },
    [fromContext, fetchNeighbor, api, endpoint, dropPk]
  );

  return {
    hasPrev: fromContext ? fromContext.prevPk != null : true,
    hasNext: fromContext ? fromContext.nextPk != null : true,
    goToPrev: () => goTo('prev'),
    goToNext: () => goTo('next')
  };
}
