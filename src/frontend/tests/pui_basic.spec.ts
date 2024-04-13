import { expect, test } from './baseFixtures.js';
import { classicUrl } from './defaults.js';

test('PUI - Basic test via django', async ({ page }) => {
  await page.goto(`${classicUrl}/platform/`);
  await expect(page).toHaveTitle('InvenTree Demo Server');
  await page.waitForURL('**/platform/');
  await page.getByLabel('username').fill('allaccess');
  await page.getByLabel('password').fill('nolimits');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform/*');
  await page.goto(`${classicUrl}/platform/`);

  await expect(page).toHaveTitle('InvenTree Demo Server');
});

test('PUI - Basic test', async ({ page }) => {
  await page.goto('./platform/');
  await expect(page).toHaveTitle('InvenTree');
  await page.waitForURL('**/platform/');
  await page.getByLabel('username').fill('allaccess');
  await page.getByLabel('password').fill('nolimits');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform');
  await page.goto('./platform/');

  await expect(page).toHaveTitle('InvenTree');
});
