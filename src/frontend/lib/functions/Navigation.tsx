import type { NavigateFunction } from 'react-router-dom';
import { ModelInformationDict } from '../enums/ModelInformation';
import type { ModelType } from '../enums/ModelType';
import { cancelEvent } from './Events';

export const getBaseUrl = (): string =>
  (window as any).INVENTREE_SETTINGS?.base_url || 'web';

/**
 * Returns the detail view URL for a given model type
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

  if (eventModified(event)) {
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

/**
 * Check if the event is modified (e.g. ctrl, shift, or meta key pressed)
 * @param event - The event to check
 * @returns true if the event was modified
 */
export const eventModified = (
  event: React.MouseEvent<HTMLButtonElement | HTMLAnchorElement>
) => {
  return event?.ctrlKey || event?.shiftKey || event?.metaKey;
};
