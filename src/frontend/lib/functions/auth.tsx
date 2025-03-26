/*
 * Authentication / login functionality
 * Note: These functions should not be exposed to the plugin library
 */

import type { NavigateFunction } from 'react-router-dom';

export function followRedirect(navigate: NavigateFunction, redirect: any) {
  let url = redirect?.redirectUrl ?? '/home';

  if (redirect?.queryParams) {
    // Construct and append query parameters
    url = `${url}?${new URLSearchParams(redirect.queryParams).toString()}`;
  }

  navigate(url);
}

/*
 * Return the value of the CSRF cookie, if available
 */
export function getCsrfCookie() {
  const cookieValue = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrftoken='))
    ?.split('=')[1];

  return cookieValue;
}

/*
 * Clear out the CSRF and session cookies (force session logout)
 */
export function clearCsrfCookie() {
  document.cookie =
    'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
}
