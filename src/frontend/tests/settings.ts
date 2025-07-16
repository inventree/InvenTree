import { expect } from 'playwright/test';

import { apiUrl } from './defaults';

/*
 * Set the value of a global setting in the database
 */
export const setSettingState = async ({
  request,
  setting,
  value
}: {
  request: any;
  setting: string;
  value: any;
}) => {
  const url = new URL(`settings/global/${setting}/`, apiUrl).toString();

  const response = await request.patch(url, {
    data: {
      value: value
    },
    headers: {
      // Basic username: password authorization
      Authorization: `Basic ${btoa('admin:inventree')}`
    }
  });

  expect(await response.status()).toBe(200);
};

export const setPluginState = async ({
  request,
  plugin,
  state
}: {
  request: any;
  plugin: string;
  state: boolean;
}) => {
  const url = new URL(`plugins/${plugin}/activate/`, apiUrl).toString();

  const response = await request.patch(url, {
    data: {
      active: state
    },
    headers: {
      // Basic username: password authorization
      Authorization: `Basic ${btoa('admin:inventree')}`
    }
  });

  expect(await response.status()).toBe(200);
};
