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

/*
 * Perform a quick login based on passing URL parameters
 */
export const doCachedLogin = async (
  browser: Browser,
  username?: string,
  password?: string,
  url?: string
): Promise<Page> => {
  username = username ?? user.username;
  password = password ?? user.password;
  url = url ?? baseUrl;

  // Cache the login state locally - and share between tests
  const fn = path.resolve(`./playwright/auth/${username}.json`);

  if (fs.existsSync(fn)) {
    const page = await browser.newPage({
      storageState: fn
    });
    console.log(`Using cached login state for ${username}`);
    await navigate(page, '/login/');
    await page.waitForURL('**/web/home**');
    await page.waitForLoadState('load');
    return page;
  }

  // Create a new blank page
  const page = await browser.newPage();

  // Ensure we are logged out first
  await doLogout(page);

  console.log(`No cache found - logging in for ${username}`);

  await navigate(page, `${url}/login?login=${username}&password=${password}`);
  await page.waitForURL('**/web/home');

  await page.getByLabel('navigation-menu').waitFor({ timeout: 5000 });
  await page.getByText(/InvenTree Demo Server -/).waitFor();

  // Wait for the dashboard to load
  await page.getByText('No widgets selected').waitFor();
  await page.waitForLoadState('load');

  // Cache the login state
  await page.context().storageState({ path: fn });

  return page;
};

export const doLogout = async (page) => {
  await navigate(page, 'logout');
  await page.waitForURL('**/web/login');
};
