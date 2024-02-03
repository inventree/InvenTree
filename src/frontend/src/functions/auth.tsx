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
 * If login is successful, a CSRF cookie will be set - which can be used to authenticate future requests.
 */
export const doBasicLogin = async (username: string, password: string) => {
  const { host } = useLocalState.getState();

  if (username.length == 0 || password.length == 0) {
    return;
  }

  // Login to the server
  await axios
    .get(apiUrl(ApiEndpoints.user_token), {
      auth: { username, password },
      baseURL: host,
      timeout: 2000
    })
    .then((response) => {
      if (response.status == 200) {
        afterLogin();
      }
    })
    .catch(() => {});
};

/**
 * Logout the user from the current session
 */
export const doLogout = async (navigate: any) => {
  // Logout from the server session
  await api.post(apiUrl(ApiEndpoints.user_logout));

  // Logout from this session
  clearCsrfCookie();
  afterLogin();

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
    if (!no_redirect) navigate('/login');
  };

  if (getCsrfCookie()) {
    // Try to login using the CSRF cookie
    api
      .get(apiUrl(ApiEndpoints.user_token))
      .then((response) => {
        if (response.status == 200) {
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
 * Check if a CSRF cookie is available
 */
export function hasToken() {
  return !!getCsrfCookie();
}

/*
 * Clear out the CSRF cookie (force session logout)
 */
export function clearCsrfCookie() {
  document.cookie =
    'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
}

/*
 * Perform any required actions after a successful login
 */
export function afterLogin() {
  setApiDefaults();
  fetchGlobalStates();

  console.log('Login successful');
}
