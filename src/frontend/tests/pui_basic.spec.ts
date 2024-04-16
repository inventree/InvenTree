import { expect, test } from './baseFixtures.js';
import { classicUrl, user } from './defaults.js';

test('PUI - Basic test via django', async ({ page }) => {
  await page.goto(`${classicUrl}/platform/logout/`);
  await page.goto(`${classicUrl}/platform/login/`);
  await expect(page).toHaveTitle('InvenTree Demo Server');
  await page.waitForURL('**/platform/login');
  await page.getByLabel('username').fill(user.username);
  await page.getByLabel('password').fill(user.password);
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform/*');
  await page.goto(`${classicUrl}/platform/`);

  await expect(page).toHaveTitle('InvenTree Demo Server');
});

test('PUI - Basic test', async ({ page }) => {
  await page.goto('./platform/logout/');
  await page.goto('./platform/login/');
  await expect(page).toHaveTitle('InvenTree');
  await page.waitForURL('**/platform/login');
  await page.getByLabel('username').fill(user.username);
  await page.getByLabel('password').fill(user.password);
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform/home');
  await page.goto('./platform/');

  await expect(page).toHaveTitle('InvenTree');
});
