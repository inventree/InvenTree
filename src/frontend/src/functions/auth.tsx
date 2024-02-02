import { t } from '@lingui/macro';
import { notifications } from '@mantine/notifications';
import { IconCheck } from '@tabler/icons-react';
import axios from 'axios';

import { api, setApiDefaults } from '../App';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from '../states/ApiState';
import { useLocalState } from '../states/LocalState';
import { useSessionState } from '../states/SessionState';

const tokenName: string = 'inventree-web-app';

/**
 * Attempt to login using username:password combination.
 * If login is successful, an API token will be returned.
 * This API token is used for any future API requests.
 */
export const doBasicLogin = async (username: string, password: string) => {
  const { host } = useLocalState.getState();
  // const apiState = useServerApiState.getState();

  if (username.length == 0 || password.length == 0) {
    return;
  }

  // At this stage, we can assume that we are not logged in, and we have no token
  useSessionState.getState().clearToken();

  // Request new token from the server
  await axios
    .get(apiUrl(ApiEndpoints.user_token), {
      auth: { username, password },
      baseURL: host,
      timeout: 2000,
      params: {
        name: tokenName
      }
    })
    .then((response) => {
      if (response.status == 200 && response.data.token) {
        // A valid token has been returned - save, and login
        useSessionState.getState().setToken(response.data.token);
      }
    })
    .catch(() => {});
};

/**
 * Logout the user from the current session
 *
 * @arg deleteToken: If true, delete the token from the server
 */
export const doLogout = async (navigate: any) => {
  // Logout from the server session
  await api.post(apiUrl(ApiEndpoints.user_logout));

  // Logout from this session
  // Note that clearToken() then calls setApiDefaults()
  clearCsrfCookie();
  useSessionState.getState().clearToken();

  notifications.hide('login');
  notifications.show({
    id: 'login',
    title: t`Logout successful`,
    message: t`You have been logged out`,
    color: 'green',
    icon: <IconCheck size="1rem" />
  });

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

export function handleReset(navigate: any, values: { email: string }) {
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

/**
 * Check login state, and redirect the user as required.
 *
 * The user may be logged in via the following methods:
 * - An existing API token is stored in the session
 * - An existing CSRF cookie is stored in the browser
 */
export function checkLoginState(
  navigate: any,
  redirect?: string,
  no_redirect?: boolean
) {
  setApiDefaults();

  // Callback function when login is successful
  const loginSuccess = () => {
    notifications.hide('login');
    notifications.show({
      id: 'login',
      title: t`Logged In`,
      message: t`Found an existing login - welcome back!`,
      color: 'green',
      icon: <IconCheck size="1rem" />
    });
    navigate(redirect ?? '/home');
  };

  // Callback function when login fails
  const loginFailure = () => {
    useSessionState.getState().clearToken();
    if (!no_redirect) navigate('/login');
  };

  if (useSessionState.getState().hasToken()) {
    // An existing token is available - check if it works
    api
      .get(apiUrl(ApiEndpoints.user_me), {
        timeout: 2000
      })
      .then((val) => {
        if (val.status === 200) {
          // Success: we are logged in (and we already have a token)
          loginSuccess();
        } else {
          loginFailure();
        }
      })
      .catch(() => {
        loginFailure();
      });
  } else if (getCsrfCookie()) {
    // Try to fetch a new token using the CSRF cookie
    api
      .get(apiUrl(ApiEndpoints.user_token), {
        params: {
          name: tokenName
        }
      })
      .then((response) => {
        if (response.status == 200 && response.data.token) {
          useSessionState.getState().setToken(response.data.token);
          loginSuccess();
        } else {
          loginFailure();
        }
      })
      .catch(() => {
        loginFailure();
      });
  } else {
    // No token, no cookie - redirect to login page
    loginFailure();
  }
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
 * Clear out the CSRF cookie (force session logout)
 */
export function clearCsrfCookie() {
  document.cookie =
    'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
}
