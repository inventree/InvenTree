import { expect, test } from './baseFixtures.js';

test('PUI - Quick Command - no keys', async ({ page }) => {
  await page.goto('./platform/');
  await expect(page).toHaveTitle('InvenTree');
  await page.waitForURL('**/platform/');
  await page.getByLabel('username').fill('allaccess');
  await page.getByLabel('password').fill('nolimits');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform');

  await expect(page).toHaveTitle('InvenTree');
  await page.waitForURL('**/platform');
  // wait for the page to load - 0.5s
  await page.waitForTimeout(500);

  // Open Spotlight with Button
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page.getByRole('button', { name: 'Home Go to the home page' }).click();
  await page
    .getByRole('heading', { name: 'Welcome to your Dashboard,' })
    .click();
  await page.waitForURL('**/platform');

  // Use navigation menu
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page
    .getByRole('button', { name: 'Open Navigation Open the main' })
    .click();
  // assert the nav headers are visible
  await page.getByRole('heading', { name: 'Navigation' }).click();
  await page.getByRole('heading', { name: 'Pages' }).click();
  await page.getByRole('heading', { name: 'Documentation' }).click();
  await page.getByRole('heading', { name: 'About' }).click();
});
