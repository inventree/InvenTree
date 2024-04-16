import { t } from '@lingui/macro';
import { notifications } from '@mantine/notifications';
import axios from 'axios';

import { api, setApiDefaults } from '../App';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from '../states/ApiState';
import { useLocalState } from '../states/LocalState';
import { fetchGlobalStates } from '../states/states';
import { showLoginNotification } from './notifications';

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

  const login_url = apiUrl(ApiEndpoints.user_login);

  // Attempt login with
  await api
    .post(
      login_url,
      {
        username: username,
        password: password
      },
      {
        baseURL: host
      }
    )
    .then((response) => {
      switch (response.status) {
        case 200:
          fetchGlobalStates();
          break;
        default:
          clearCsrfCookie();
          break;
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
  await api.post(apiUrl(ApiEndpoints.user_logout)).finally(() => {
    clearCsrfCookie();
    navigate('/login');

    showLoginNotification({
      title: t`Logged Out`,
      message: t`Successfully logged out`
    });
  });
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

  if (redirect == '/') {
    redirect = '/home';
  }

  // Callback function when login is successful
  const loginSuccess = () => {
    showLoginNotification({
      title: t`Logged In`,
      message: t`Successfully logged in`
    });

    navigate(redirect ?? '/home');
  };

  // Callback function when login fails
  const loginFailure = () => {
    if (!no_redirect) {
      navigate('/login', { state: { redirectFrom: redirect } });
    }
  };

  // Check the 'user_me' endpoint to see if the user is logged in
  if (isLoggedIn()) {
    api
      .get(apiUrl(ApiEndpoints.user_me))
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

export function isLoggedIn() {
  return !!getCsrfCookie();
}

/*
 * Clear out the CSRF and session cookies (force session logout)
 */
export function clearCsrfCookie() {
  document.cookie =
    'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
}
