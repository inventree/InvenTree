import { expect, test } from './baseFixtures.js';
import { baseUrl, logoutUrl, user } from './defaults.js';
import { doLogin, doQuickLogin } from './login.js';

test('Login - Basic Test', async ({ page }) => {
  await doLogin(page);

  // Check that the username is provided
  await page.getByText(user.username);

  await expect(page).toHaveTitle(/^InvenTree/);

  // Go to the dashboard
  await page.goto(baseUrl);
  await page.waitForURL('**/platform');

  await page.getByText('InvenTree Demo Server -').waitFor();

  // Check that the username is provided
  await page.getByText(user.username);

  await expect(page).toHaveTitle(/^InvenTree/);

  // Go to the dashboard
  await page.goto(baseUrl);
  await page.waitForURL('**/platform');

  // Logout (via menu)
  await page.getByRole('button', { name: 'Ally Access' }).click();
  await page.getByRole('menuitem', { name: 'Logout' }).click();

  await page.waitForURL('**/platform/login');
  await page.getByLabel('username');
});

test('Login - Quick Test', async ({ page }) => {
  await doQuickLogin(page);

  // Check that the username is provided
  await page.getByText(user.username);

  await expect(page).toHaveTitle(/^InvenTree/);

  // Go to the dashboard
  await page.goto(baseUrl);
  await page.waitForURL('**/platform');

  await page.getByText('InvenTree Demo Server - ').waitFor();

  // Logout (via URL)
  await page.goto(`${baseUrl}/logout/`);
  await page.waitForURL('**/platform/login');
  await page.getByLabel('username');
});

/**
 * Test various types of login failure
 */
test('Login - Failures', async ({ page }) => {
  const loginWithError = async () => {
    await page.getByRole('button', { name: 'Log In' }).click();
    await page.getByText('Login failed').waitFor();
    await page.getByText('Check your input and try again').waitFor();
    await page.locator('#login').getByRole('button').click();
  };

  // Navigate to the 'login' page
  await page.goto(logoutUrl);
  await expect(page).toHaveTitle(/^InvenTree.*$/);
  await page.waitForURL('**/platform/login');

  // Attempt login with invalid credentials
  await page.getByLabel('login-username').fill('invalid user');
  await page.getByLabel('login-password').fill('invalid password');

  await loginWithError();

  // Attempt login with valid (but disabled) user
  await page.getByLabel('login-username').fill('ian');
  await page.getByLabel('login-password').fill('inactive');

  await loginWithError();

  // Attempt login with no username
  await page.getByLabel('login-username').fill('');
  await page.getByLabel('login-password').fill('hunter2');

  await loginWithError();

  // Attempt login with no password
  await page.getByLabel('login-username').fill('ian');
  await page.getByLabel('login-password').fill('');

  await loginWithError();

  await page.waitForTimeout(2500);
});
