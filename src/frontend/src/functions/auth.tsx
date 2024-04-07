import { t } from '@lingui/macro';
import { notifications } from '@mantine/notifications';
import { IconCheck } from '@tabler/icons-react';
import axios from 'axios';

import { api, setApiDefaults } from '../App';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from '../states/ApiState';
import { useLocalState } from '../states/LocalState';
import { fetchGlobalStates } from '../states/states';

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

  clearCsrfCookie();

  // Attempt login with
  await axios
    .get(apiUrl(ApiEndpoints.user_login), {
      auth: { username, password },
      baseURL: host,
      timeout: 2000,
      withCredentials: true,
      xsrfCookieName: 'csrftoken,sessionid'
    })
    .then((response) => {
      if (response.status == 200) {
        fetchGlobalStates();
      } else {
        clearCsrfCookie();
      }
    })
    .catch(() => {
      clearCsrfCookie();
    });
};

/**
 * Logout the user from the current session
 *
 * @arg deleteToken: If true, delete the token from the server
 */
export const doLogout = async (navigate: any) => {
  // Logout from the server session
  await api.post(apiUrl(ApiEndpoints.user_logout)).catch(() => {
    // If an error occurs here, we are likely already logged out
    clearCsrfCookie();
    navigate('/login');
    return;
  });

  // Logout from this session
  // Note that clearToken() then calls setApiDefaults()
  clearCsrfCookie();

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
    if (!no_redirect) {
      navigate('/login', { state: { redirectFrom: redirect } });
    }
  };

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

export function isLoggedIn() {
  let cookie = getCsrfCookie();
  console.log('isLoggedIn:', !!cookie, cookie);

  return !!getCsrfCookie();
}

/*
 * Clear out the CSRF and session cookies (force session logout)
 */
export function clearCsrfCookie() {
  console.log('clearing cookies');

  document.cookie =
    'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  ('csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;');
}
