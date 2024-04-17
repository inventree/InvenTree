import { expect, test } from './baseFixtures.js';
import { classicUrl, user } from './defaults.js';

const BASE_URL = `${classicUrl}/platform`;

test('PUI - Basic test via django', async ({ page }) => {
  await page.goto(`${BASE_URL}/logout/`, { timeout: 5000 });
  await page.goto(`${BASE_URL}/login/`, { timeout: 5000 });
  await expect(page).toHaveTitle(RegExp('^InvenTree.*$'));
  await page.getByLabel('username').fill(user.username);
  await page.getByLabel('password').fill(user.password);
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform/*');
  await page.goto(`${BASE_URL}/home`, { timeout: 5000 });

  await expect(page).toHaveTitle('InvenTree Demo Server');
});

test('PUI - Basic test', async ({ page }) => {
  await page.goto(`${BASE_URL}/logout`);
  await page.goto(`${BASE_URL}/login`);
  await expect(page).toHaveTitle(RegExp('^InvenTree.*$'));
  await page.waitForURL('**/platform/login');
  await page.getByLabel('username').fill(user.username);
  await page.getByLabel('password').fill(user.password);
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform/home');
  await page.goto(`${BASE_URL}/home`);

  await expect(page).toHaveTitle(RegExp('^InvenTree'));
});
