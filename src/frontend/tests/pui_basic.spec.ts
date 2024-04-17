import { expect, test } from './baseFixtures.js';
import { baseUrl, loginUrl, logoutUrl, user } from './defaults.js';

test('PUI - Basic Login Test', async ({ page }) => {
  await page.goto(logoutUrl);
  await page.goto(loginUrl);
  await expect(page).toHaveTitle(RegExp('^InvenTree.*$'));
  await page.waitForURL('**/platform/login');
  await page.getByLabel('username').fill(user.username);
  await page.getByLabel('password').fill(user.password);
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform/home');

  await page.waitForTimeout(1000);

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
