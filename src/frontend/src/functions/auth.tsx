import { t } from '@lingui/macro';
import { notifications, showNotification } from '@mantine/notifications';
import { IconCheck } from '@tabler/icons-react';
import axios from 'axios';

import { api } from '../App';
import { ApiPaths } from '../enums/ApiEndpoints';
import { apiUrl, useServerApiState } from '../states/ApiState';
import { useLocalState } from '../states/LocalState';
import { useSessionState } from '../states/SessionState';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../states/SettingsState';
import { useUserState } from '../states/UserState';

export const doClassicLogin = async (username: string, password: string) => {
  const { host } = useLocalState.getState();

  // Get token from server
  const token = await axios
    .get(apiUrl(ApiPaths.user_token), {
      auth: { username, password },
      baseURL: host,
      timeout: 2000,
      params: {
        name: 'inventree-web-app'
      }
    })
    .then((response) => response.data.token)
    .catch((error) => {
      showNotification({
        title: t`Login failed`,
        message: t`Error fetching token from server.`,
        color: 'red'
      });
      return false;
    });

  if (token === false) return token;

  // log in with token
  doTokenLogin(token);
  return true;
};

/**
 * Logout the user (invalidate auth token)
 */
export const doClassicLogout = async () => {
  // TODO @matmair - logout from the server session
  // Set token in context
  const { setToken } = useSessionState.getState();
  setToken(undefined);

  notifications.show({
    title: t`Logout successful`,
    message: t`See you soon.`,
    color: 'green',
    icon: <IconCheck size="1rem" />
  });

  return true;
};

export const doSimpleLogin = async (email: string) => {
  const { host } = useLocalState.getState();
  const mail = await axios
    .post(apiUrl(ApiPaths.user_simple_login), {
      email: email
    })
    .then((response) => response.data)
    .catch((_error) => {
      return false;
    });
  return mail;
};

// Perform a login using a token
export const doTokenLogin = (token: string) => {
  const { setToken } = useSessionState.getState();
  const { fetchUserState } = useUserState.getState();
  const { fetchServerApiState } = useServerApiState.getState();
  const globalSettingsState = useGlobalSettingsState.getState();
  const userSettingsState = useUserSettingsState.getState();

  setToken(token);
  fetchUserState();
  fetchServerApiState();
  globalSettingsState.fetchSettings();
  userSettingsState.fetchSettings();
};

export function handleReset(navigate: any, values: { email: string }) {
  api
    .post(apiUrl(ApiPaths.user_reset), values, {
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
 * Check login state, and redirect the user as required
 */
export function checkLoginState(navigate: any, redirect?: string) {
  api
    .get(apiUrl(ApiPaths.user_token), {
      timeout: 2000,
      params: {
        name: 'inventree-web-app'
      }
    })
    .then((val) => {
      if (val.status === 200 && val.data.token) {
        doTokenLogin(val.data.token);

        notifications.show({
          title: t`Already logged in`,
          message: t`Found an existing login - using it to log you in.`,
          color: 'green',
          icon: <IconCheck size="1rem" />
        });
        navigate(redirect ?? '/home');
      } else {
        navigate('/login');
      }
    })
    .catch(() => {
      navigate('/login');
    });
}
