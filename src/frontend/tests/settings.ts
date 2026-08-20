import { expect } from 'playwright/test';

import { createApi } from './api';

/*
 * Set the value of a global setting in the database
 */
export const setSettingState = async ({
  setting,
  value,
  type = 'global',
  plugin
}: {
  setting: string;
  value: any;
  type?: 'global' | 'plugin';
  plugin?: string;
}) => {
  const api = await createApi({});
  const url =
    type === 'global'
      ? `settings/global/${setting}/`
      : `plugins/${plugin}/settings/${setting}/`;
  const response = await api.patch(url, {
    data: {
      value: value
    }
  });

  expect(response.status()).toBe(200);
};

export const setPluginState = async ({
  plugin,
  state
}: {
  plugin: string;
  state: boolean;
}) => {
  const api = await createApi({});
  const response = await api.patch(`plugins/${plugin}/activate/`, {
    data: {
      active: state
    }
  });

  expect(response.status()).toBe(200);
};
