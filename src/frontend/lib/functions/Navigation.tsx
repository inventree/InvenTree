import type { NavigateFunction } from 'react-router-dom';
import { ModelInformationDict } from '../enums/ModelInformation';
import type { ModelType } from '../enums/ModelType';
import { apiUrl } from './Api';
import { cancelEvent } from './Events';

export const getBaseUrl = (): string =>
  (window as any).INVENTREE_SETTINGS?.base_url || 'web';

/**
 * Returns the detail view URL for a given model type.
 * This is the UI URL, not the API URL.
 */
export function getDetailUrl(
  model: ModelType,
  pk: number | string,
  absolute?: boolean
): string {
  const modelInfo = ModelInformationDict[model];

  if (pk === undefined || pk === null) {
    return '';
  }

  if (!!pk && modelInfo && modelInfo.url_detail) {
    const url = modelInfo.url_detail.replace(':pk', pk.toString());
    const base = getBaseUrl();

    if (absolute && base) {
      return `/${base}${url}`;
    } else {
      return url;
    }
  }

  console.error(`No detail URL found for model ${model} <${pk}>`);
  return '';
}

/**
 * Returns the API detail URL for a given model type.
 */
export function getApiUrl(
  model: ModelType,
  pk: number | string
): string | undefined {
  const modelInfo = ModelInformationDict[model];

  if (pk === undefined || pk === null) {
    return '';
  }

  if (!!pk && modelInfo && modelInfo.api_endpoint) {
    return apiUrl(modelInfo.api_endpoint, pk);
  }

  console.error(`No API detail URL found for model ${model} <${pk}>`);
  return undefined;
}

/*
 * Navigate to a provided link.
 * - If the link is to be opened externally, open it in a new tab.
 * - Otherwise, navigate using the provided navigate function.
 */
export const navigateToLink = (
  link: string,
  navigate: NavigateFunction,
  event: any
) => {
  cancelEvent(event);

  const base = `/${getBaseUrl()}`;

  if (event?.ctrlKey || event?.shiftKey) {
    // Open the link in a new tab
    let url = link;
    if (link.startsWith('/') && !link.startsWith(base)) {
      url = `${base}${link}`;
    }
    window.open(url, '_blank');
  } else {
    // Navigate internally
    let url = link;

    if (link.startsWith(base)) {
      // Strip the base URL from the link
      url = link.replace(base, '');
    }

    navigate(url);
  }
};
