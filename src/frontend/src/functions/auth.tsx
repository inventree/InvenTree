import { t } from '@lingui/macro';
import { notifications } from '@mantine/notifications';
import { IconCheck } from '@tabler/icons-react';
import axios from 'axios';

import { ApiPaths, url, useApiState } from '../states/ApiState';
import { useLocalState } from '../states/LocalState';
import { useSessionState } from '../states/SessionState';

export const doClassicLogin = async (username: string, password: string) => {
  const { host } = useLocalState.getState();

  // Get token from server
  const token = await axios
    .get(`${host}${url(ApiPaths.user_token)}`, { auth: { username, password } })
    .then((response) => response.data.token)
    .catch((error) => {
      return false;
    });

  if (token === false) return token;

  // log in with token
  doTokenLogin(token);
  return true;
};

export const doClassicLogout = async () => {
  // TODO @matmair - logout from the server session
  // Set token in context
  const { setToken } = useSessionState.getState();
  setToken(undefined);

  notifications.show({
    title: t`Logout successfull`,
    message: t`See you soon.`,
    color: 'green',
    icon: <IconCheck size="1rem" />
  });

  return true;
};

export const doSimpleLogin = async (email: string) => {
  const { host } = useLocalState.getState();
  const mail = await axios
    .post(`${host}${url(ApiPaths.user_simple_login)}`, {
      email: email
    })
    .then((response) => response.data)
    .catch((error) => {
      return false;
    });
  return mail;
};

export const doTokenLogin = (token: string) => {
  const { setToken } = useSessionState.getState();
  const { fetchApiState } = useApiState.getState();

  setToken(token);
  fetchApiState();
};
