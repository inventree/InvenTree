import type { Browser, Page } from '@playwright/test';
import { loginUrl, logoutUrl, user, webUrl } from './defaults';

import fs from 'node:fs';
import path from 'node:path';
import { navigate } from './helpers.js';

interface LoginOptions {
  username?: string;
  password?: string;
  baseUrl?: string;
}

/*
 * Perform form based login operation from the "login" URL
 */
export const doLogin = async (page: Page, options?: LoginOptions) => {
  const username: string = options?.username ?? user.username;
  const password: string = options?.password ?? user.password;

  console.log('- Logging in with username:', username);

  await navigate(page, loginUrl, {
    baseUrl: options?.baseUrl,
    waitUntil: 'networkidle'
  });

  await page.waitForURL('**/web/login');

  await page.getByLabel('username').fill(username);
  await page.getByLabel('password').fill(password);

  await page.waitForTimeout(100);

  await page.getByRole('button', { name: 'Log in' }).click();

  await page.waitForTimeout(100);
  await page.waitForLoadState('networkidle');

  await page.getByRole('link', { name: 'Dashboard' }).waitFor();
  await page.getByRole('button', { name: 'navigation-menu' }).waitFor();
  await page.waitForURL(/\/web(\/home)?/);
  await page.waitForLoadState('networkidle');
};

export interface CachedLoginOptions {
  username?: string;
  password?: string;
  url?: string;
  baseUrl?: string;
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

    await navigate(page, url ?? webUrl, {
      baseUrl: options?.baseUrl,
      waitUntil: 'networkidle'
    });

    await page.getByRole('link', { name: 'Dashboard' }).waitFor();
    await page.getByRole('button', { name: 'navigation-menu' }).waitFor();
    await page.waitForURL(/\/web(\/home)?/);
    await page.waitForLoadState('networkidle');

    return page;
  }

  // Create a new blank page
  const page = await browser.newPage();

  console.log(`No cache found - logging in for ${username}`);

  // Completely clear the browser cache and cookies, etc
  await page.context().clearCookies();
  await page.context().clearPermissions();

  await doLogin(page, {
    username: username,
    password: password,
    baseUrl: options?.baseUrl
  });

  await page.getByLabel('navigation-menu').waitFor({ timeout: 5000 });
  await page.waitForLoadState('load');

  // Cache the login state
  await page.context().storageState({ path: fn });

  if (url) {
    await navigate(page, url, {
      baseUrl: options?.baseUrl,
      waitUntil: 'networkidle'
    });
  }

  return page;
};

interface LogoutOptions {
  baseUrl?: string;
}

export const doLogout = async (page, options?: LogoutOptions) => {
  await navigate(page, logoutUrl, {
    baseUrl: options?.baseUrl,
    waitUntil: 'load'
  });
  await page.waitForURL('**/web/login');
};
