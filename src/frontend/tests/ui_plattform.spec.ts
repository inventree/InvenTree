import { expect, test } from '@playwright/test';

test('Basic Platform UI test', async ({ page }) => {
  await page.goto('./platform/');
  await expect(page).toHaveTitle('InvenTree Demo Server');
  await page.waitForURL('**/platform/');
  await page.getByLabel('username').fill('allaccess');
  await page.getByLabel('password').fill('nolimits');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform/home');
  await page.goto('./platform/');

  await expect(page).toHaveTitle('InvenTree Demo Server');
});
