import { cancelEvent } from '../functions/events';

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
