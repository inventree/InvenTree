import { expect } from './baseFixtures.js';
import { loginUrl, logoutUrl, user } from './defaults';

export const doLogin = async (page) => {
  await page.goto(logoutUrl);
  await page.goto(loginUrl);
  await expect(page).toHaveTitle(RegExp('^InvenTree.*$'));
  await page.waitForURL('**/platform/login');
  await page.getByLabel('username').fill(user.username);
  await page.getByLabel('password').fill(user.password);
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform/home');
  await page.waitForTimeout(1000);
};
