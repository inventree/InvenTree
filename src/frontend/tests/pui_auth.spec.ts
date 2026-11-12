/**
 * Tests for the unauthenticated "account" pages:
 * - Password reset
 * - Set password (from reset link)
 * - Email verification
 * - User registration
 */

import { expect, generateUUID, test } from './baseFixtures.js';
import { loginUrl } from './defaults.js';
import { navigate } from './helpers.js';
import { setSettingState } from './settings.js';

test('Auth - Password Reset', async ({ page }) => {
  await setSettingState({ setting: 'LOGIN_ENABLE_PWD_FORGOT', value: true });

  try {
    // Navigate to the login page, and follow the "reset password" link
    await navigate(page, loginUrl);
    await page.getByRole('button', { name: 'Reset password' }).click();
    await page.waitForURL('**/reset-password');

    await page.getByText('Reset Password').first().waitFor();
    await page.getByPlaceholder('email@example.org').fill('nobody@example.org');
    await page.getByRole('button', { name: 'Send Email' }).click();

    // Allauth reports success regardless of whether the account exists
    // Note: this also checks that the CSRF cookie is set before the request
    await page.getByText('Mail delivery successful').waitFor();
    await page.waitForURL('**/login');
  } finally {
    await setSettingState({
      setting: 'LOGIN_ENABLE_PWD_FORGOT',
      value: false
    });
  }
});

test('Auth - Set Password', async ({ page }) => {
  // No key provided - should redirect back to the login page
  await navigate(page, 'set-password');
  await page.getByText('Key invalid').first().waitFor();

  // Invalid key provided
  await navigate(page, 'set-password?key=not-a-valid-key');
  await page.getByText('Set new password').first().waitFor();
  await page.getByRole('textbox', { name: 'Password' }).fill('a-new-Passw0rd!');
  await page.getByRole('button', { name: 'Send Password' }).click();
  await page.waitForLoadState('networkidle');
});

test('Auth - Verify Email', async ({ page }) => {
  // An invalid key is rejected by the server (no redirect occurs)
  await navigate(page, 'verify-email/not-a-valid-key');
  await page.getByText('Verify Email').first().waitFor();
  await page.getByRole('button', { name: 'Verify' }).click();
  await page.waitForLoadState('networkidle');
  await expect(page).toHaveURL(/verify-email/);
});

test('Auth - Registration', async ({ page }) => {
  const username = `pw-reg-${generateUUID().slice(0, 8)}`;

  await setSettingState({ setting: 'LOGIN_ENABLE_REG', value: true });

  try {
    await navigate(page, loginUrl);
    await page.getByText("Don't have an account?").waitFor();
    await page.getByRole('button', { name: 'Register' }).click();

    // Go back to login, then return to the registration form
    await page.getByRole('button', { name: 'Go back to login' }).click();
    await page.getByRole('button', { name: 'Register' }).click();

    // Mismatched passwords
    await page.getByLabel('register-username').fill(username);
    await page.getByLabel('register-email').fill(`${username}@example.org`);
    await page.getByLabel('register-password', { exact: true }).fill('abc');
    await page.getByLabel('register-password-repeat').fill('xyz');
    await page.getByRole('button', { name: 'Register', exact: true }).click();
    await page.waitForLoadState('networkidle');

    // Valid registration
    await page
      .getByLabel('register-password', { exact: true })
      .fill('Pl@ywright-Passw0rd');
    await page
      .getByLabel('register-password-repeat')
      .fill('Pl@ywright-Passw0rd');
    await page.getByRole('button', { name: 'Register', exact: true }).click();
    await page.waitForLoadState('networkidle');
    await expect(page.getByLabel('register-username')).toBeVisible({
      visible: false
    });
  } finally {
    await setSettingState({ setting: 'LOGIN_ENABLE_REG', value: false });
  }
});
