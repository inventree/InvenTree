import { expect } from './baseFixtures.js';
import { baseUrl, loginUrl, logoutUrl, user } from './defaults';

/*
 * Perform form based login operation from the "login" URL
 */
export const doLogin = async (page) => {
  await page.goto(logoutUrl);
  await page.goto(loginUrl);
  await expect(page).toHaveTitle(RegExp('^InvenTree.*$'));
  await page.waitForURL('**/platform/login');
  await page.getByLabel('username').fill(user.username);
  await page.getByLabel('password').fill(user.password);
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform/home');
  await page.waitForTimeout(250);
};

/*
 * Perform a quick login based on passing URL parameters
 */
export const doQuickLogin = async (page) => {
  await page.goto(logoutUrl);
  await page.goto(
    `${baseUrl}/login/?login=${user.username}&password=${user.password}`
  );
  await page.waitForURL('**/platform/*');
  await page.waitForTimeout(250);
};
