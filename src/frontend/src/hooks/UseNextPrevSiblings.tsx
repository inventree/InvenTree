import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useApi } from '../contexts/ApiContext';

/**
 * Configuration for {@link useNextPrevSiblings}.
 *
 * The hook treats the API as the source of truth. To find the previous
 * instance it sends the same filter parameters plus `pk__lt=<current>`,
 * ordered descending, and asks for a single record. To find the next
 * instance it sends `pk__gt=<current>`, ordered ascending.
 *
 * Callers may override `pkField` if the underlying model uses a different
 * primary key column.
 */
export interface UseNextPrevSiblingsOptions {
  /** Model type whose detail view is rendering the buttons. */
  model: ModelType;
  /** Primary key of the currently displayed instance. */
  pk?: number | string | null;
  /**
   * Additional API filter parameters to scope the previous / next
   * lookup (e.g. `{ active: true, category: 5 }`). These should match
   * the parameters used to render the originating list, so that "next"
   * actually navigates within the visible set.
   */
  filterParams?: Record<string, unknown>;
  /** Field used by the API for primary key comparison. Defaults to `'pk'`. */
  pkField?: string;
  /** Optional explicit ordering field. Defaults to `pkField`. */
  ordering?: string;
  /** Disable the lookup entirely (e.g. while current pk is still loading). */
  enabled?: boolean;
}

/**
 * Single neighbour resolved by the hook. `null` means there is no item
 * in that direction within the supplied filter; `undefined` means the
 * lookup is still in flight.
 */
export interface NextPrevSibling {
  pk?: number | string;
  /** Best-effort human label (pulled from common display fields). */
  label?: string;
}

/**
 * Resolve the previous / next sibling of a given instance, using the
 * InvenTree REST API.
 *
 * The hook is conservative: it queries one record in each direction and
 * surfaces both neighbours as soon as the data is available. The list of
 * `params` is the API-filtered ordering context, not the API `ordering`
 * query parameter (which defaults to the primary key column).
 *
 * This intentionally avoids client-side navigation state: a list view
 * with hundreds of pages would otherwise have to load the entire page
 * just to compute "what comes next". With API filtering we only ever
 * ask for two records.
 */
export function useNextPrevSiblings({
  model,
  pk,
  filterParams,
  pkField = 'pk',
  ordering,
  enabled = true
}: UseNextPrevSiblingsOptions): {
  prev?: NextPrevSibling | null;
  next?: NextPrevSibling | null;
  isLoading: boolean;
} {
  const api = useApi();
  const modelInfo = ModelInformationDict[model];

  const orderField = ordering ?? pkField;
  const numericPk =
    pk === undefined || pk === null || pk === '' ? null : Number(pk);

  const baseParams = useMemo(() => {
    const cleaned: Record<string, unknown> = {};
    if (filterParams) {
      for (const [key, value] of Object.entries(filterParams)) {
        if (value === undefined || value === null) continue;
        cleaned[key] = value;
      }
    }
    return cleaned;
  }, [filterParams]);

  const common = useMemo(
    () => ({
      ...baseParams,
      limit: 1,
      ordering: orderField
    }),
    [baseParams, orderField]
  );

  const enabledQuery =
    enabled && numericPk !== null && !!modelInfo?.api_endpoint;

  const prevQuery = useQuery({
    enabled: enabledQuery,
    queryKey: [
      'nextprev',
      model,
      pkField,
      'prev',
      numericPk,
      JSON.stringify(baseParams),
      orderField
    ],
    queryFn: async () => {
      const url = apiUrl(modelInfo!.api_endpoint);
      const params = {
        ...common,
        [`${pkField}__lt`]: numericPk,
        ordering: `-${orderField}`
      };
      const response = await api.get(url, { params });
      const data = response?.data ?? [];
      return data.length > 0 ? data[0] : null;
    }
  });

  const nextQuery = useQuery({
    enabled: enabledQuery,
    queryKey: [
      'nextprev',
      model,
      pkField,
      'next',
      numericPk,
      JSON.stringify(baseParams),
      orderField
    ],
    queryFn: async () => {
      const url = apiUrl(modelInfo!.api_endpoint);
      const params = {
        ...common,
        [`${pkField}__gt`]: numericPk,
        ordering: orderField
      };
      const response = await api.get(url, { params });
      const data = response?.data ?? [];
      return data.length > 0 ? data[0] : null;
    }
  });

  const pickLabel = useMemo(() => {
    return (record: any): string | undefined => {
      if (!record) return undefined;
      return (
        record.full_name ??
        record.name ??
        record.description ??
        record.username ??
        record.IPN ??
        record.reference ??
        record.title
      );
    };
  }, []);

  const prev = useMemo<NextPrevSibling | null | undefined>(() => {
    if (!enabledQuery) return undefined;
    if (prevQuery.isLoading) return undefined;
    if (!prevQuery.data) return null;
    const record = prevQuery.data;
    const value = record[pkField];
    if (value === undefined || value === null) return null;
    return { pk: value, label: pickLabel(record) };
  }, [enabledQuery, prevQuery.isLoading, prevQuery.data, pkField, pickLabel]);

  const next = useMemo<NextPrevSibling | null | undefined>(() => {
    if (!enabledQuery) return undefined;
    if (nextQuery.isLoading) return undefined;
    if (!nextQuery.data) return null;
    const record = nextQuery.data;
    const value = record[pkField];
    if (value === null || value === undefined) return null;
    return { pk: value, label: pickLabel(record) };
  }, [enabledQuery, nextQuery.isLoading, nextQuery.data, pkField, pickLabel]);

  return {
    prev,
    next,
    isLoading:
      (prevQuery.isLoading && prev === undefined) ||
      (nextQuery.isLoading && next === undefined)
  };
}
