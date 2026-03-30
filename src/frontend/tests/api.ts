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
      Authorization: `Basic ${btoa(`${username || adminuser.username}:${password || adminuser.password}`)}`
    }
  });
