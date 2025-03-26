import type { ModelType } from '../enums/ModelType';
import { ModelInformationDict } from '../enums/ModelType';
import { cancelEvent } from '../functions/events';
import { useLocalState } from '../states/LocalState';

export const getBaseUrl = (): string => {
  return window.INVENTREE_SETTINGS.base_url || 'web';
};

/*
 * Navigate to a provided link.
 * - If the link is to be opened externally, open it in a new tab.
 * - Otherwise, navigate using the provided navigate function.
 */
export const navigateToLink = (link: string, navigate: any, event: any) => {
  cancelEvent(event);

  if (event?.ctrlKey || event?.shiftKey) {
    // Open the link in a new tab
    const url = `/${getBaseUrl()}${link}`;
    window.open(url, '_blank');
  } else {
    // Navigate internally
    navigate(link);
  }
};

/**
 * Returns the edit view URL for a given model type
 */
export function generateUrl(url: string | URL, base?: string): string {
  const { host } = useLocalState.getState();

  let newUrl: string | URL = url;

  try {
    if (base) {
      newUrl = new URL(url, base).toString();
    } else if (host) {
      newUrl = new URL(url, host).toString();
    } else {
      newUrl = url.toString();
    }
  } catch (e: any) {
    console.error(`ERR: generateURL failed. url='${url}', base='${base}'`);
  }

  return newUrl.toString();
}

/**
 * Returns the detail view URL for a given model type.
 * This is the URL for viewier the details of a single object in the UI
 */
export function getDetailUrl(
  model: ModelType,
  pk: number | string,
  base_url?: string,
  absolute?: boolean
): string {
  const modelInfo = ModelInformationDict[model];

  if (pk === undefined || pk === null) {
    return '';
  }

  if (!!pk && modelInfo && modelInfo.url_detail) {
    const url = modelInfo.url_detail.replace(':pk', pk.toString());
    const base = base_url;

    if (absolute && base) {
      return `/${base}${url}`;
    } else {
      return url;
    }
  }

  // Fallback to console error
  console.error(`No detail URL found for model ${model} <${pk}>`);
  return '';
}
