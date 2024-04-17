import { expect, test } from './baseFixtures.js';
import { homeUrl, loginUrl, logoutUrl, user } from './defaults.js';

test('PUI - Basic test via django', async ({ page }) => {
  await page.goto(logoutUrl, { timeout: 5000 });
  await page.goto(loginUrl, { timeout: 5000 });
  await expect(page).toHaveTitle(RegExp('^InvenTree.*$'));
  await page.getByLabel('username').fill(user.username);
  await page.getByLabel('password').fill(user.password);
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform/*');
  await page.goto(homeUrl, { timeout: 5000 });

  await expect(page).toHaveTitle('InvenTree Demo Server');
});

test('PUI - Basic test', async ({ page }) => {
  await page.goto(logoutUrl);
  await page.goto(loginUrl);
  await expect(page).toHaveTitle(RegExp('^InvenTree.*$'));
  await page.waitForURL('**/platform/login');
  await page.getByLabel('username').fill(user.username);
  await page.getByLabel('password').fill(user.password);
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform/home');
  await page.goto(homeUrl);

  await expect(page).toHaveTitle(RegExp('^InvenTree'));
});
