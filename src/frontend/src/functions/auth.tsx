import { t } from '@lingui/macro';
import { notifications } from '@mantine/notifications';
import axios from 'axios';
import type { AxiosRequestConfig } from 'axios';
import type { Location, NavigateFunction } from 'react-router-dom';
import { api, setApiDefaults } from '../App';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from '../states/ApiState';
import { useLocalState } from '../states/LocalState';
import { useUserState } from '../states/UserState';
import { type Provider, fetchGlobalStates } from '../states/states';
import { showLoginNotification } from './notifications';

export function followRedirect(navigate: NavigateFunction, redirect: any) {
  let url = redirect?.redirectUrl ?? '/home';

  if (redirect?.queryParams) {
    // Construct and appand query parameters
    url = `${url}?${new URLSearchParams(redirect.queryParams).toString()}`;
  }

  navigate(url);
}

/**
 * sends a request to the specified url from a form. this will change the window location.
 * @param {string} path the path to send the post request to
 * @param {object} params the parameters to add to the url
 * @param {string} [method=post] the method to use on the form
 *
 * Source https://stackoverflow.com/questions/133925/javascript-post-request-like-a-form-submit/133997#133997
 */

function post(path: string, params: any, method = 'post') {
  const form = document.createElement('form');
  form.method = method;
  form.action = path;

  for (const key in params) {
    if (
      params.hasOwn?.(key) ||
      Object.prototype.hasOwnProperty.call(params, key)
    ) {
      const hiddenField = document.createElement('input');
      hiddenField.type = 'hidden';
      hiddenField.name = key;
      hiddenField.value = params[key];

      form.appendChild(hiddenField);
    }
  }

  document.body.appendChild(form);
  form.submit();
}

/**
 * Attempt to login using username:password combination.
 * If login is successful, an API token will be returned.
 * This API token is used for any future API requests.
 */
export const doBasicLogin = async (
  username: string,
  password: string,
  navigate: NavigateFunction
) => {
  const { host } = useLocalState.getState();
  const { clearUserState, setToken, fetchUserState } = useUserState.getState();

  if (username.length == 0 || password.length == 0) {
    return;
  }

  clearCsrfCookie();
  await ensureCsrf();

  let loginDone = false;
  let success = false;

  // Attempt login with
  await api
    .post(
      apiUrl(ApiEndpoints.auth_login),
      {
        username: username,
        password: password
      },
      {
        baseURL: host
      }
    )
    .then((response) => {
      if (response.status == 200 && response.data?.meta?.is_authenticated) {
        setToken(response.data.meta.access_token);
        loginDone = true;
        success = true;
      }
    })
    .catch((err) => {
      if (err?.response?.status == 401) {
        const mfa_flow = err.response.data.data.flows.find(
          (flow: any) => flow.id == 'mfa_authenticate'
        );
        if (mfa_flow && mfa_flow.is_pending == true) {
          success = true;
          navigate('/mfa');
        }
      }
    });

  if (loginDone) {
    await fetchUserState();
    fetchGlobalStates();
  } else if (!success) {
    clearUserState();
  }
  return success;
};

/**
 * Logout the user from the current session
 *
 * @arg deleteToken: If true, delete the token from the server
 */
export const doLogout = async (navigate: NavigateFunction) => {
  const { clearUserState, isLoggedIn } = useUserState.getState();

  // Logout from the server session
  if (isLoggedIn() || !!getCsrfCookie()) {
    await authApi(apiUrl(ApiEndpoints.auth_session), undefined, 'delete').catch(
      () => {}
    );
    showLoginNotification({
      title: t`Logged Out`,
      message: t`Successfully logged out`
    });
  }

  clearUserState();
  clearCsrfCookie();
  navigate('/login');
};

export const doSimpleLogin = async (email: string) => {
  const { host } = useLocalState.getState();
  const mail = await axios
    .post(
      apiUrl(ApiEndpoints.user_simple_login),
      {
        email: email
      },
      {
        baseURL: host,
        timeout: 2000
      }
    )
    .then((response) => response.data)
    .catch((_error) => {
      return false;
    });
  return mail;
};

export async function ensureCsrf() {
  const cookie = getCsrfCookie();
  if (cookie == undefined) {
    await api.get(apiUrl(ApiEndpoints.user_token)).catch(() => {});
  }
}

export function handleReset(
  navigate: NavigateFunction,
  values: { email: string }
) {
  api
    .post(apiUrl(ApiEndpoints.user_reset), values, {
      headers: { Authorization: '' }
    })
    .then((val) => {
      if (val.status === 200) {
        notifications.show({
          title: t`Mail delivery successful`,
          message: t`Check your inbox for a reset link. This only works if you have an account. Check in spam too.`,
          color: 'green',
          autoClose: false
        });
        navigate('/login');
      } else {
        notifications.show({
          title: t`Reset failed`,
          message: t`Check your input and try again.`,
          color: 'red'
        });
      }
    });
}

export function handleMfaLogin(
  navigate: NavigateFunction,
  location: Location<any>,
  values: { code: string }
) {
  const { setToken } = useUserState.getState();
  authApi(apiUrl(ApiEndpoints.auth_login_2fa), undefined, 'post', {
    code: values.code
  }).then((response) => {
    setToken(response.data.meta.access_token);
    followRedirect(navigate, location?.state);
  });
}

/**
 * Check login state, and redirect the user as required.
 *
 * The user may be logged in via the following methods:
 * - An existing API token is stored in the session
 * - An existing CSRF cookie is stored in the browser
 */
export const checkLoginState = async (
  navigate: any,
  redirect?: any,
  no_redirect?: boolean
) => {
  setApiDefaults();

  if (redirect == '/') {
    redirect = '/home';
  }

  const { isLoggedIn, fetchUserState } = useUserState.getState();

  // Callback function when login is successful
  const loginSuccess = () => {
    showLoginNotification({
      title: t`Logged In`,
      message: t`Successfully logged in`
    });

    fetchGlobalStates();

    followRedirect(navigate, redirect);
  };

  // Callback function when login fails
  const loginFailure = () => {
    if (!no_redirect) {
      navigate('/login', { state: redirect });
    }
  };

  if (isLoggedIn()) {
    // Already logged in
    loginSuccess();
    return;
  }

  // Not yet logged in, but we might have a valid session cookie
  // Attempt to login
  await fetchUserState();

  if (isLoggedIn()) {
    loginSuccess();
  } else {
    loginFailure();
  }
};

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

export function ProviderLogin(
  provider: Provider,
  process: 'login' | 'connect' = 'login'
) {
  const { host } = useLocalState.getState();
  // TODO
  const loc = window.location;
  const values = {
    provider: provider.id,
    callback_url: 'http://localhost:8000/logged-in',
    process: process,
    csrfmiddlewaretoken: getCsrfCookie()
  };
  const url = `${host}${apiUrl(ApiEndpoints.auth_provider_redirect)}`;
  post(url, values);
}

/**
 * Makes an API request with session tokens using the provided URL, configuration, method, and data.
 *
 * @param url - The URL to which the request is sent.
 * @param config - Optional Axios request configuration.
 * @param method - The HTTP method to use for the request. Defaults to 'get'.
 * @param data - Optional data to be sent with the request.
 * @returns A promise that resolves to the response of the API request.
 */
export function authApi(
  url: string,
  config: AxiosRequestConfig | undefined = undefined,
  method: 'get' | 'post' | 'put' | 'delete' = 'get',
  data?: any
) {
  const requestConfig = config || {};

  // set method
  requestConfig.method = method;

  // set data
  if (data) {
    requestConfig.data = data;
  }

  // use normal api
  return api(url, requestConfig);
}
