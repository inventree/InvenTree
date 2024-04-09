import { expect, test } from './baseFixtures.js';

test('PUI - Quick Command', async ({ page }) => {
  await page.goto('./platform/');
  await expect(page).toHaveTitle('InvenTree');
  await page.waitForURL('**/platform/');
  await page.getByLabel('username').fill('allaccess');
  await page.getByLabel('password').fill('nolimits');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform');
  await page.goto('./platform/');

  await expect(page).toHaveTitle('InvenTree');
  await page.waitForURL('**/platform/');
  // wait for the page to load - 0.5s
  await page.waitForTimeout(500);

  // Open Spotlight with Keyboard Shortcut
  await page.keyboard.press('Control+K');
  await page.getByText('Go to the InvenTree dashboard').click();
  await page
    .locator('div')
    .filter({ hasText: /^Dashboard$/ })
    .click();
  await page.waitForURL('**/platform/dashboard');

  // Open Spotlight with Button
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page.getByText('Go to the home page').click();
  await page
    .getByRole('heading', { name: 'Welcome to your Dashboard,' })
    .click();
  await page.waitForURL('**/platform');

  // Open Spotlight with Keyboard Shortcut and Search
  await page.keyboard.press('Control+K');
  await page.getByPlaceholder('Search...').fill('Dashboard');
  await page.getByPlaceholder('Search...').press('Tab');
  await page.getByPlaceholder('Search...').press('Enter');
  await page.waitForURL('**/platform/dashboard');

  // Reset
  await page.goto('./platform/');

  // Use navigation menu
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page.getByText('Open Navigation').click();
  // assert the nav headers are visible
  await page.getByRole('heading', { name: 'Navigation' }).click();
  await page.getByRole('heading', { name: 'Pages' }).click();
  await page.getByRole('heading', { name: 'Documentation' }).click();
  await page.getByRole('heading', { name: 'About' }).click();
});
