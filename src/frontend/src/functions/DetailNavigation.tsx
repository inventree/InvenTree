import type { MouseEvent } from 'react';

export const DETAIL_NAVIGATION_PARAMS = {
  api: '_na',
  query: '_nq',
  index: '_ni',
  pk: '_np',
  field: '_nf'
} as const;

const LEGACY_DETAIL_NAVIGATION_PARAMS = {
  api: '_nav_api',
  query: '_nav_query',
  index: '_nav_index',
  pk: '_nav_pk',
  field: '_nav_field'
} as const;

const PAGINATION_PARAMS = new Set(['limit', 'offset', 'page']);
const DEFAULT_DETAIL_NAVIGATION_FIELD = 'pk';

// Keep common built-in list endpoints compact while preserving the full URL
// for plugin and otherwise unknown endpoints.
const DETAIL_NAVIGATION_API_ALIASES: Record<string, string> = {
  '/api/part/': 'p',
  '/api/part/category/': 'pc',
  '/api/stock/': 's',
  '/api/stock/location/': 'sl',
  '/api/build/': 'b',
  '/api/build/line/': 'bl',
  '/api/build/item/': 'bi',
  '/api/company/': 'c',
  '/api/company/part/': 'sp',
  '/api/company/part/manufacturer/': 'mp',
  '/api/order/po/': 'po',
  '/api/order/po-line/': 'pol',
  '/api/order/so/': 'so',
  '/api/order/so-line/': 'sol',
  '/api/order/so/shipment/': 'sh',
  '/api/order/ro/': 'ro',
  '/api/order/ro-line/': 'rol',
  '/api/order/transfer-order/': 'to',
  '/api/order/transfer-order-line/': 'tol',
  '/api/order/transfer-order-allocation/': 'toa',
  '/api/order/so-allocation/': 'soa',
  '/api/bom/': 'bom',
  '/api/parameter/': 'pa',
  '/api/parameter/template/': 'pt',
  '/api/user/': 'u',
  '/api/user/group/': 'ug',
  '/api/project-code/': 'pr',
  '/api/tag/': 'tag',
  '/api/attachment/': 'at',
  '/api/machine/': 'm'
};

const DETAIL_NAVIGATION_API_URLS = new Map(
  Object.entries(DETAIL_NAVIGATION_API_ALIASES).map(([url, alias]) => [
    alias,
    url
  ])
);

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

type DetailNavigationParam = keyof typeof DETAIL_NAVIGATION_PARAMS;

function getDetailNavigationParam(
  params: URLSearchParams,
  key: DetailNavigationParam
): string | null {
  return (
    params.get(DETAIL_NAVIGATION_PARAMS[key]) ??
    params.get(LEGACY_DETAIL_NAVIGATION_PARAMS[key])
  );
}

function encodeDetailNavigationApi(apiUrl: string): string {
  return DETAIL_NAVIGATION_API_ALIASES[apiUrl] ?? apiUrl;
}

function decodeDetailNavigationApi(apiUrl: string): string {
  return DETAIL_NAVIGATION_API_URLS.get(apiUrl) ?? apiUrl;
}

function removeDetailNavigationParams(params: URLSearchParams) {
  Object.values(DETAIL_NAVIGATION_PARAMS).forEach((key) => {
    params.delete(key);
  });

  Object.values(LEGACY_DETAIL_NAVIGATION_PARAMS).forEach((key) => {
    params.delete(key);
  });
}

function setDetailNavigationParams(
  target: URL,
  {
    apiUrl,
    query,
    index,
    pk,
    field
  }: {
    apiUrl: string;
    query: string;
    index: number;
    pk: string | number;
    field: string;
  }
) {
  removeDetailNavigationParams(target.searchParams);

  target.searchParams.set(
    DETAIL_NAVIGATION_PARAMS.api,
    encodeDetailNavigationApi(apiUrl)
  );
  target.searchParams.set(DETAIL_NAVIGATION_PARAMS.index, String(index));
  target.searchParams.set(DETAIL_NAVIGATION_PARAMS.pk, String(pk));

  if (field !== DEFAULT_DETAIL_NAVIGATION_FIELD) {
    target.searchParams.set(DETAIL_NAVIGATION_PARAMS.field, field);
  }

  if (query) {
    target.searchParams.set(DETAIL_NAVIGATION_PARAMS.query, query);
  }
}

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

  query.append(key, value.toString());
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

  setDetailNavigationParams(target, {
    apiUrl,
    query,
    index,
    pk,
    field
  });

  return `${target.pathname}${target.search}${target.hash}`;
}

export function readDetailNavigationContext(
  search: string
): DetailNavigationContext | null {
  const params = new URLSearchParams(search);
  const encodedApiUrl = getDetailNavigationParam(params, 'api');
  const apiUrl = encodedApiUrl
    ? decodeDetailNavigationApi(encodedApiUrl)
    : null;
  const query = getDetailNavigationParam(params, 'query') ?? '';
  const index = Number(getDetailNavigationParam(params, 'index'));
  const pk = getDetailNavigationParam(params, 'pk');
  const field =
    getDetailNavigationParam(params, 'field') ??
    DEFAULT_DETAIL_NAVIGATION_FIELD;

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
  const target = new URL(`${nextPath}${search}`, 'https://inventree.local');

  setDetailNavigationParams(target, {
    apiUrl: context.apiUrl,
    query: context.query.toString(),
    index: targetIndex,
    pk: targetPk,
    field: context.field
  });

  return `${target.pathname}${target.search}${target.hash}`;
}
