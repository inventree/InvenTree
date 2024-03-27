import { classicUrl } from './baseFixtures';
import { expect, test } from './baseFixtures.js';

test('Basic Platform UI test via django', async ({ page }) => {
  await page.goto(`${classicUrl}/platform/`);
  await expect(page).toHaveTitle('InvenTree Demo Server');
  await page.waitForURL('**/platform/');
  await page.getByLabel('username').fill('allaccess');
  await page.getByLabel('password').fill('nolimits');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform');
  await page.goto(`${classicUrl}/platform/`);

  await expect(page).toHaveTitle('InvenTree Demo Server');
});

test('Basic Platform UI test', async ({ page }) => {
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
