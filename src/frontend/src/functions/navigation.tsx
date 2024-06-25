import { base_url } from '../main';
import { cancelEvent } from './events';

/*
 * Navigate to a provided link.
 * - If the link is to be opened externally, open it in a new tab.
 * - Otherwise, navigate using the provided navigate function.
 */
export const navigateToLink = (link: string, navigate: any, event: any) => {
  cancelEvent(event);

  if (event?.ctrlKey || event?.shiftKey) {
    // Open the link in a new tab
    const url = `/${base_url}${link}`;
    window.open(url, '_blank');
  } else {
    // Navigate internally
    navigate(link);
  }
};
