import { expect, test } from './baseFixtures.js';
import { logoutUrl } from './defaults.js';
import { navigate } from './helpers.js';
import { doLogin } from './login.js';

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
  await navigate(page, logoutUrl);
  await expect(page).toHaveTitle(/^InvenTree.*$/);
  await page.waitForURL('**/web/login');

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
});

test('Login - Change Password', async ({ page }) => {
  await doLogin(page, 'noaccess', 'youshallnotpass');

  // Navigate to the 'change password' page
  await navigate(page, 'settings/user/account', { waitUntil: 'networkidle' });
  await page.getByLabel('action-menu-account-actions').click();
  await page.getByLabel('action-menu-account-actions-change-password').click();

  // First attempt with some errors
  await page.getByLabel('password', { exact: true }).fill('youshallnotpass');
  await page.getByLabel('input-password-1').fill('12345');
  await page.getByLabel('input-password-2').fill('54321');
  await page.getByRole('button', { name: 'Confirm' }).click();
  await page.getByText('The two password fields didn’t match').waitFor();

  await page.getByLabel('input-password-2').clear();
  await page.getByLabel('input-password-2').fill('12345');
  await page.getByRole('button', { name: 'Confirm' }).click();

  await page.getByText('This password is too short').waitFor();
  await page.getByText('This password is entirely numeric').waitFor();

  await page.waitForTimeout(250);

  await page.getByLabel('password', { exact: true }).clear();
  await page.getByLabel('input-password-1').clear();
  await page.getByLabel('input-password-2').clear();

  await page.getByLabel('password', { exact: true }).fill('youshallnotpass');
  await page.getByLabel('input-password-1').fill('youshallnotpass');
  await page.getByLabel('input-password-2').fill('youshallnotpass');

  await page.getByRole('button', { name: 'Confirm' }).click();

  await page.getByText('Password Changed').waitFor();
  await page.getByText('The password was set successfully').waitFor();
});
