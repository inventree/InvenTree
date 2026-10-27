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

  // find tip and patch out ftu
  try {
    const response = await api.get('user/me/');
    if (!response.ok()) return;
    const tip = ((await response.json())?.tips ?? []).find(
      (t: any) => t.tip_id === 'org.inventree.i.tip.ftug'
    );
    if (tip && !tip.finished) {
      await api.patch(`user/me/tips/${tip.pk}/`, {
        data: { finished: true }
      });
    }
  } finally {
    await api.dispose();
  }
};
