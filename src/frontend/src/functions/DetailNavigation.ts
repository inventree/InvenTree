/**
 * URL state used to restore a table context on a detail page.
 *
 * The context deliberately contains an API list URL and its query rather than
 * a page of records. This keeps shared links compact, survives a browser
 * restart, and lets the server remain the source of truth for sorting and
 * filtering.
 */
export const DETAIL_NAVIGATION_PARAMS = {
  api: '_detail_nav_api',
  query: '_detail_nav_query',
  index: '_detail_nav_index',
  pk: '_detail_nav_pk',
  field: '_detail_nav_field'
} as const;

const PAGINATION_PARAMS = new Set(['limit', 'offset', 'page']);

export type DetailNavigationContext = {
  apiUrl: string;
  query: URLSearchParams;
  index: number;
  pk: string;
  field: string;
};

export type DetailNavigationTarget = {
  href: string;
  index: number;
};

export function isDetailNavigationParam(key: string): boolean {
  return Object.values(DETAIL_NAVIGATION_PARAMS).includes(
    key as (typeof DETAIL_NAVIGATION_PARAMS)[keyof typeof DETAIL_NAVIGATION_PARAMS]
  );
}

export function isSafeApiListUrl(url?: string): url is string {
  return !!url && url.startsWith('/api/') && !url.startsWith('//');
}

function appendQueryValue(query: URLSearchParams, key: string, value: unknown) {
  if (
    value === null ||
    value === undefined ||
    PAGINATION_PARAMS.has(key) ||
    isDetailNavigationParam(key)
  ) {
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
  const target = new URL(detailUrl, 'https://inventree.local');
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
): DetailNavigationContext | undefined {
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
    return undefined;
  }

  return {
    apiUrl,
    query: new URLSearchParams(query),
    index,
    pk,
    field
  };
}

function replaceDetailPk(
  pathname: string,
  currentPk: string,
  targetPk: string | number
): string | undefined {
  const segments = pathname.split('/');
  const currentValue = String(currentPk);

  for (let index = segments.length - 1; index >= 0; index--) {
    let segment = segments[index];

    try {
      segment = decodeURIComponent(segment);
    } catch {
      continue;
    }

    if (segment === currentValue) {
      segments[index] = encodeURIComponent(String(targetPk));
      return segments.join('/');
    }
  }

  return undefined;
}

export function buildDetailNavigationTarget(
  pathname: string,
  search: string,
  context: DetailNavigationContext,
  targetPk: string | number,
  targetIndex: number
): DetailNavigationTarget | undefined {
  const nextPath = replaceDetailPk(pathname, context.pk, targetPk);

  if (!nextPath) {
    return undefined;
  }

  const target = new URL(`${nextPath}${search}`, 'https://inventree.local');

  target.searchParams.set(DETAIL_NAVIGATION_PARAMS.index, String(targetIndex));
  target.searchParams.set(DETAIL_NAVIGATION_PARAMS.pk, String(targetPk));

  return {
    href: `${target.pathname}${target.search}${target.hash}`,
    index: targetIndex
  };
}
