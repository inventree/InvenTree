import { t } from '@lingui/macro';
import { notifications, showNotification } from '@mantine/notifications';
import { IconCheck } from '@tabler/icons-react';
import axios from 'axios';

import { api } from '../App';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl, useServerApiState } from '../states/ApiState';
import { useLocalState } from '../states/LocalState';
import { useSessionState } from '../states/SessionState';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../states/SettingsState';
import { useGlobalStatusState } from '../states/StatusState';
import { useUserState } from '../states/UserState';

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
  useSessionState.getState().setToken('');
  useSessionState.getState().setLoggedIn(false);

  // Request new token from the server
  await axios
    .get(apiUrl(ApiEndpoints.user_token), {
      auth: { username, password },
      baseURL: host,
      timeout: 2500,
      params: {
        name: 'inventree-web-app'
      }
    })
    .then((response) => {
      if (response.status == 200) {
        if (response.data?.token) {
          // A valid token has been returned - save, and login
          useSessionState.getState().setToken(response.data.token);
          useSessionState.getState().setLoggedIn(true);
        }
      }
    })
    .catch(() => {});
};

/**
 * Logout the user from the current session
 *
 * @arg deleteToken: If true, delete the token from the server
 */
export const doClassicLogout = async (deleteToken?: boolean) => {
  if (deleteToken) {
    // Logout from the server session
    await api.post(apiUrl(ApiEndpoints.user_logout));
  }

  // Logout from this session
  useSessionState.getState().setToken('');
  useSessionState.getState().setLoggedIn(false);

  notifications.show({
    title: t`Logout successful`,
    message: t`You have been logged out`,
    color: 'green',
    icon: <IconCheck size="1rem" />
  });

  return true;
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
        timeout: 2500
      }
    )
    .then((response) => response.data)
    .catch((_error) => {
      return false;
    });
  return mail;
};

/*
 * Perform a login using a token
 */
export const doTokenLogin = (token: string) => {
  const { setToken } = useSessionState.getState();
  const { fetchUserState } = useUserState.getState();
  const { fetchServerApiState } = useServerApiState.getState();
  const globalSettingsState = useGlobalSettingsState.getState();
  const globalStatusState = useGlobalStatusState.getState();
  const userSettingsState = useUserSettingsState.getState();

  // First, set the API token for auth
  setToken(token);

  // Fetch user and server data
  fetchUserState();
  fetchServerApiState();

  // Fetch settings
  globalStatusState.fetchStatus();
  globalSettingsState.fetchSettings();
  userSettingsState.fetchSettings();
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
 * If there is no token available in the session, then the user is *not* logged in.
 * If there is a token available, we need to test it!
 */
export function checkLoginState(
  navigate: any,
  redirect?: string,
  no_redirect?: boolean
) {
  if (!useSessionState.getState().token) {
    // No token available - redirect to the login page
    if (!no_redirect) navigate('/login');
  }

  // There *is* a token available: Test if it is valid
  api
    .get(apiUrl(ApiEndpoints.user_me), {
      timeout: 2500
    })
    .then((val) => {
      if (val.status === 200) {
        // Success: we are logged in!
        useSessionState().setLoggedIn(true);

        notifications.show({
          title: t`Logged In`,
          message: t`Found an existing login - welcome back!`,
          color: 'green',
          icon: <IconCheck size="1rem" />
        });
        navigate(redirect ?? '/home');
      } else {
        if (!no_redirect) navigate('/login');
      }
    })
    .catch(() => {
      if (!no_redirect) navigate('/login');
    });
}
