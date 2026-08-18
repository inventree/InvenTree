import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { MouseEvent } from 'react';

export const DETAIL_NAVIGATION_PARAMS = {
  api: '_na',
  query: '_nq',
  index: '_ni',
  pk: '_np',
  field: '_nf'
} as const;

const DETAIL_NAVIGATION_PARAM_KEYS = new Set<string>(
  Object.values(DETAIL_NAVIGATION_PARAMS)
);
const PAGINATION_PARAMS = new Set(['limit', 'offset', 'page']);
const DEFAULT_DETAIL_NAVIGATION_FIELD = 'pk';

// Keep common built-in list endpoints compact while preserving the full URL
// for plugin and otherwise unknown endpoints.
const DETAIL_NAVIGATION_API_ALIASES = new Map<string, string>([
  [apiUrl(ApiEndpoints.part_list), 'p'],
  [apiUrl(ApiEndpoints.category_list), 'pc'],
  [apiUrl(ApiEndpoints.stock_item_list), 's'],
  [apiUrl(ApiEndpoints.stock_location_list), 'sl'],
  [apiUrl(ApiEndpoints.build_order_list), 'b'],
  [apiUrl(ApiEndpoints.build_line_list), 'bl'],
  [apiUrl(ApiEndpoints.build_item_list), 'bi'],
  [apiUrl(ApiEndpoints.company_list), 'c'],
  [apiUrl(ApiEndpoints.supplier_part_list), 'sp'],
  [apiUrl(ApiEndpoints.manufacturer_part_list), 'mp'],
  [apiUrl(ApiEndpoints.purchase_order_list), 'po'],
  [apiUrl(ApiEndpoints.purchase_order_line_list), 'pol'],
  [apiUrl(ApiEndpoints.sales_order_list), 'so'],
  [apiUrl(ApiEndpoints.sales_order_line_list), 'sol'],
  [apiUrl(ApiEndpoints.sales_order_shipment_list), 'sh'],
  [apiUrl(ApiEndpoints.return_order_list), 'ro'],
  [apiUrl(ApiEndpoints.return_order_line_list), 'rol'],
  [apiUrl(ApiEndpoints.transfer_order_list), 'to'],
  [apiUrl(ApiEndpoints.transfer_order_line_list), 'tol'],
  [apiUrl(ApiEndpoints.transfer_order_allocation_list), 'toa'],
  [apiUrl(ApiEndpoints.sales_order_allocation_list), 'soa'],
  [apiUrl(ApiEndpoints.bom_list), 'bom'],
  [apiUrl(ApiEndpoints.parameter_list), 'pa'],
  [apiUrl(ApiEndpoints.parameter_template_list), 'pt'],
  [apiUrl(ApiEndpoints.user_list), 'u'],
  [apiUrl(ApiEndpoints.group_list), 'ug'],
  [apiUrl(ApiEndpoints.project_code_list), 'pr'],
  [apiUrl(ApiEndpoints.tag_list), 'tag'],
  [apiUrl(ApiEndpoints.attachment_list), 'at'],
  [apiUrl(ApiEndpoints.machine_list), 'm']
]);

const DETAIL_NAVIGATION_API_URLS = new Map(
  Array.from(DETAIL_NAVIGATION_API_ALIASES.entries()).map(([url, alias]) => [
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
  return params.get(DETAIL_NAVIGATION_PARAMS[key]);
}

function encodeDetailNavigationApi(apiUrl: string): string {
  return DETAIL_NAVIGATION_API_ALIASES.get(apiUrl) ?? apiUrl;
}

function decodeDetailNavigationApi(apiUrl: string): string {
  return DETAIL_NAVIGATION_API_URLS.get(apiUrl) ?? apiUrl;
}

function removeDetailNavigationParams(params: URLSearchParams) {
  DETAIL_NAVIGATION_PARAM_KEYS.forEach((key) => {
    params.delete(key);
  });
}

function filterDetailNavigationParams(
  params: URLSearchParams,
  includeDetailNavigationParams: boolean
): URLSearchParams {
  const filteredParams = new URLSearchParams();

  for (const [key, value] of params) {
    if (
      DETAIL_NAVIGATION_PARAM_KEYS.has(key) === includeDetailNavigationParams
    ) {
      filteredParams.append(key, value);
    }
  }

  return filteredParams;
}

export function excludeDetailNavigationParams(
  params: URLSearchParams
): URLSearchParams {
  return filterDetailNavigationParams(params, false);
}

export function extractDetailNavigationParams(
  params: URLSearchParams
): URLSearchParams {
  return filterDetailNavigationParams(params, true);
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
