import { expect, test } from './baseFixtures.js';
import { baseUrl, user } from './defaults.js';
import { doLogin, doQuickLogin } from './login.js';

test('PUI - Basic Login Test', async ({ page }) => {
  await doLogin(page);

  // Check that the username is provided
  await page.getByText(user.username);

  await expect(page).toHaveTitle(RegExp('^InvenTree'));

  // Go to the dashboard
  await page.goto(baseUrl);
  await page.waitForURL('**/platform');

  await page
    .getByRole('heading', { name: `Welcome to your Dashboard, ${user.name}` })
    .click();
});

test('PUI - Quick Login Test', async ({ page }) => {
  await doQuickLogin(page);

  // Check that the username is provided
  await page.getByText(user.username);

  await expect(page).toHaveTitle(RegExp('^InvenTree'));

  // Go to the dashboard
  await page.goto(baseUrl);
  await page.waitForURL('**/platform');

  await page
    .getByRole('heading', { name: `Welcome to your Dashboard, ${user.name}` })
    .click();
});
