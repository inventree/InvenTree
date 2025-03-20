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
