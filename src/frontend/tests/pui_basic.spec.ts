import { expect, test } from './baseFixtures.js';
import { baseUrl, classicUrl, logoutUrl, user } from './defaults.js';
import { doLogin, doQuickLogin } from './login.js';

test('PUI - Basic login test via django', async ({ page }) => {
  await page.goto(logoutUrl);
  await page.goto(`${classicUrl}/platform/`);
  await expect(page).toHaveTitle('InvenTree Demo Server');
  await page.waitForURL('**/platform/');
  await page.getByLabel('username').fill(user.username);
  await page.getByLabel('password').fill(user.password);
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform/*');
  await page.goto(`${classicUrl}/platform/`);

  await expect(page).toHaveTitle('InvenTree Demo Server');
});

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
