import type { Browser, Page } from '@playwright/test';
import { expect } from './baseFixtures.js';
import { user } from './defaults';
import { navigate } from './helpers.js';

import fs from 'node:fs';
import path from 'node:path';

/*
 * Perform form based login operation from the "login" URL
 */
export const doLogin = async (page, username?: string, password?: string) => {
  username = username ?? user.username;
  password = password ?? user.password;

  console.log('- Logging in with username:', username);

  await navigate(page, '/logout/');

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

// Set of users allowed to do cached login
// This is to prevent tests from running with the wrong user
const ALLOWED_USERS: string[] = ['admin', 'allaccess', 'reader', 'steven'];

/*
 * Perform a quick login based on passing URL parameters
 */
export const doCachedLogin = async (
  browser: Browser,
  options?: CachedLoginOptions
): Promise<Page> => {
  const username = options?.username ?? user.username;
  const password = options?.password ?? user.password;
  const url = options?.url ?? '';

  // FAIL if an unsupported username is provided
  if (!ALLOWED_USERS.includes(username)) {
    throw new Error(`Invalid username provided to doCachedLogin: ${username}`);
  }

  // Cache the login state locally - and share between tests
  const fn = path.resolve(`./playwright/auth/${username}.json`);

  if (fs.existsSync(fn)) {
    const page = await browser.newPage({
      storageState: fn
    });
    console.log(`Using cached login state for ${username}`);
    await navigate(page, 'http://localhost:5173/web/');
    await navigate(page, url);
    await page.waitForURL('**/web/**');
    await page.waitForLoadState('load');
    return page;
  }

  // Create a new blank page
  const page = await browser.newPage();

  console.log(`No cache found - logging in for ${username}`);

  // Completely clear the browser cache and cookies, etc
  await page.context().clearCookies();
  await page.context().clearPermissions();

  // Ensure we start from the login page
  await navigate(page, 'http://localhost:5173/web/');

  await doLogin(page, username, password);
  await page.getByLabel('navigation-menu').waitFor({ timeout: 5000 });
  await page.getByText(/InvenTree Demo Server -/).waitFor();
  await page.waitForURL('**/web/**');

  // Wait for the dashboard to load
  //await page.getByText('No widgets selected').waitFor()
  await page.waitForLoadState('load');

  // Cache the login state
  await page.context().storageState({ path: fn });

  if (url) {
    await navigate(page, url);
  }

  return page;
};

export const doLogout = async (page) => {
  await navigate(page, '/logout');
  await page.waitForURL('**/web/login');
};
