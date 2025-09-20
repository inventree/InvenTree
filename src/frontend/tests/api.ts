import { request } from '@playwright/test';
import { adminuser, apiUrl } from './defaults';

export const createApi = () =>
  request.newContext({
    baseURL: apiUrl,
    extraHTTPHeaders: {
      Authorization: `Basic ${btoa(`${adminuser.username}:${adminuser.password}`)}`
    }
  });
