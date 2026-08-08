import type { MouseEvent } from 'react';

export const DETAIL_NAVIGATION_PARAMS = {
  api: '_nav_api',
  query: '_nav_query',
  index: '_nav_index',
  pk: '_nav_pk',
  field: '_nav_field'
} as const;

const PAGINATION_PARAMS = new Set(['limit', 'offset', 'page']);

export type DetailNavigationContext = {
  apiUrl: string;
  query: URLSearchParams;
  index: number;
  pk: string;
  field: string;
};

export type DetailNavigationAction = {
  href: string;
  onClick: (event: MouseEvent<HTMLAnchorElement>) => void;
};

export function isSafeApiListUrl(url?: string): url is string {
  return !!url && url.startsWith('/api/') && !url.startsWith('//');
}

function appendQueryValue(query: URLSearchParams, key: string, value: unknown) {
  if (value === null || value === undefined || PAGINATION_PARAMS.has(key)) {
    return;
  }

  if (Array.isArray(value)) {
    value.forEach((item) => appendQueryValue(query, key, item));
    return;
  }

  if (typeof value === 'object') {
    query.append(key, JSON.stringify(value));
    return;
  }

  query.append(key, String(value));
}

export function serializeDetailNavigationQuery(
  params: Record<string, unknown>
): string {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    appendQueryValue(query, key, value);
  });

  return query.toString();
}

export function buildDetailNavigationUrl({
  detailUrl,
  apiUrl,
  queryParams,
  index,
  pk,
  field
}: {
  detailUrl: string;
  apiUrl: string;
  queryParams: Record<string, unknown>;
  index: number;
  pk: string | number;
  field: string;
}): string {
  const target = new URL(detailUrl, 'http://inventree.local');
  const query = serializeDetailNavigationQuery(queryParams);

  target.searchParams.set(DETAIL_NAVIGATION_PARAMS.api, apiUrl);
  target.searchParams.set(DETAIL_NAVIGATION_PARAMS.index, String(index));
  target.searchParams.set(DETAIL_NAVIGATION_PARAMS.pk, String(pk));
  target.searchParams.set(DETAIL_NAVIGATION_PARAMS.field, field);

  if (query) {
    target.searchParams.set(DETAIL_NAVIGATION_PARAMS.query, query);
  }

  return `${target.pathname}${target.search}${target.hash}`;
}

export function readDetailNavigationContext(
  search: string
): DetailNavigationContext | null {
  const params = new URLSearchParams(search);
  const apiUrl = params.get(DETAIL_NAVIGATION_PARAMS.api);
  const query = params.get(DETAIL_NAVIGATION_PARAMS.query) ?? '';
  const index = Number(params.get(DETAIL_NAVIGATION_PARAMS.index));
  const pk = params.get(DETAIL_NAVIGATION_PARAMS.pk);
  const field = params.get(DETAIL_NAVIGATION_PARAMS.field) ?? 'pk';

  if (
    !apiUrl ||
    !isSafeApiListUrl(apiUrl) ||
    !Number.isInteger(index) ||
    index < 0 ||
    pk === null
  ) {
    return null;
  }

  return {
    apiUrl,
    query: new URLSearchParams(query),
    index,
    pk,
    field
  };
}

export function replaceDetailPk(
  pathname: string,
  currentPk: string,
  targetPk: string | number
): string {
  const segments = pathname.split('/');
  const currentValue = String(currentPk);
  const targetValue = encodeURIComponent(String(targetPk));
  let replaced = false;

  const nextSegments = segments.map((segment) => {
    if (!replaced && decodeURIComponent(segment) === currentValue) {
      replaced = true;
      return targetValue;
    }

    return segment;
  });

  return replaced ? nextSegments.join('/') : pathname;
}

export function buildDetailNavigationTarget(
  pathname: string,
  search: string,
  context: DetailNavigationContext,
  targetPk: string | number,
  targetIndex: number
): string {
  const nextPath = replaceDetailPk(pathname, context.pk, targetPk);
  const target = new URL(`${nextPath}${search}`, 'http://inventree.local');

  target.searchParams.set(DETAIL_NAVIGATION_PARAMS.index, String(targetIndex));
  target.searchParams.set(DETAIL_NAVIGATION_PARAMS.pk, String(targetPk));

  return `${target.pathname}${target.search}${target.hash}`;
}
