import type { Browser, Page } from '@playwright/test';
import { expect } from './baseFixtures.js';
import { baseUrl, logoutUrl, user } from './defaults';
import { navigate } from './helpers.js';

import fs from 'node:fs';
import path from 'node:path';

/*
 * Perform form based login operation from the "login" URL
 */
export const doLogin = async (page, username?: string, password?: string) => {
  username = username ?? user.username;
  password = password ?? user.password;

  await navigate(page, logoutUrl);
  await expect(page).toHaveTitle(/^InvenTree.*$/);
  await page.waitForURL('**/web/login');
  await page.getByLabel('username').fill(username);
  await page.getByLabel('password').fill(password);
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/web/home');
  await page.waitForTimeout(250);
};

export interface CachedLoginOptions {
  username?: string;
  password?: string;
  url?: string;
}

/*
 * Perform a quick login based on passing URL parameters
 */
export const doCachedLogin = async (
  browser: Browser,
  options?: CachedLoginOptions
): Promise<Page> => {
  const username = options?.username ?? user.username;
  const password = options?.password ?? user.password;
  const url = options?.url ?? baseUrl;

  // FAIL if any of the following usernames are provided
  // This is to prevent tests from running with the wrong user
  // Some usernames are reserved for specific tests
  if (['noaccess', 'ian', 'susan', 'reader'].includes(username)) {
    throw new Error(`Cannot run tests with reserved username: ${username}`);
  }

  // Cache the login state locally - and share between tests
  const fn = path.resolve(`./playwright/auth/${username}.json`);

  if (fs.existsSync(fn)) {
    const page = await browser.newPage({
      storageState: fn
    });
    console.log(`Using cached login state for ${username}`);
    await navigate(page, url);
    await page.waitForURL('**/web/**');
    await page.waitForLoadState('load');
    return page;
  }

  // Create a new blank page
  const page = await browser.newPage();

  // Ensure we are logged out first
  // await doLogout(page);

  console.log(`No cache found - logging in for ${username}`);

  await doLogin(page, username, password);
  await page.getByLabel('navigation-menu').waitFor({ timeout: 5000 });
  await page.getByText(/InvenTree Demo Server -/).waitFor();
  await page.waitForURL('**/web/**');
  // await navigate(page, `/login?login=${username}&password=${password}`);
  // awaiit

  // Wait for the dashboard to load
  await page.getByText('No widgets selected').waitFor();
  await page.waitForLoadState('load');

  // Cache the login state
  await page.context().storageState({ path: fn });

  await navigate(page, url);
  return page;
};

export const doLogout = async (page) => {
  await navigate(page, 'logout');
  await page.waitForURL('**/web/login');
};
