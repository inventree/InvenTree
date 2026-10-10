import { request } from '@playwright/test';
import { adminuser, apiUrl } from './defaults';

export const createApi = ({
  username,
  password
}: {
  username?: string;
  password?: string;
}) =>
  request.newContext({
    baseURL: apiUrl,
    extraHTTPHeaders: {
      Authorization: `Basic ${btoa(`${username || adminuser.username}:${password || adminuser.testcred}`)}`
    }
  });

export const dismissFtu = async ({
  username,
  password
}: {
  username: string;
  password: string;
}) => {
  const api = await createApi({ username, password });

  // find tipp and patch out ftu
  try {
    const response = await api.get('user/me/');
    if (!response.ok()) return;
    const tipp = ((await response.json())?.tipps ?? []).find(
      (t: any) => t.tipp_id === 'org.inventree.i.tipp.ftue'
    );
    if (tipp && !tipp.finished) {
      await api.patch(`user/me/tipps/${tipp.pk}/`, {
        data: { finished: true }
      });
    }
  } finally {
    await api.dispose();
  }
};
