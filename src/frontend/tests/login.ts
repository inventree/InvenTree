import { expect } from './baseFixtures.js';
import { baseUrl, logoutUrl, user } from './defaults';
import { navigate } from './helpers.js';

/*
 * Perform form based login operation from the "login" URL
 */
export const doLogin = async (page, username?: string, password?: string) => {
  username = username ?? user.username;
  password = password ?? user.password;

  await navigate(page, logoutUrl);
  await expect(page).toHaveTitle(/^InvenTree.*$/);
  await page.waitForURL('**/platform/login');
  await page.getByLabel('username').fill(username);
  await page.getByLabel('password').fill(password);
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform/home');
  await page.waitForTimeout(250);
};

/*
 * Perform a quick login based on passing URL parameters
 */
export const doQuickLogin = async (
  page,
  username?: string,
  password?: string,
  url?: string
) => {
  username = username ?? user.username;
  password = password ?? user.password;
  url = url ?? baseUrl;

  await navigate(page, `${url}/login?login=${username}&password=${password}`);
  await page.waitForURL('**/platform/home');

  await page.getByLabel('navigation-menu').waitFor({ timeout: 5000 });
  await page.getByText(/InvenTree Demo Server -/).waitFor();

  // Wait for the dashboard to load
  await page.getByText('No widgets selected').waitFor();
  await page.waitForTimeout(250);
};

export const doLogout = async (page) => {
  await navigate(page, 'logout');
  await page.waitForURL('**/platform/login');
};
