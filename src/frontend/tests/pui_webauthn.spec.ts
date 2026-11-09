/**
 * Tests for WebAuthn (security key / passkey) multi-factor authentication.
 *
 * A Chromium "virtual authenticator" (via the DevTools protocol) is used
 * to emulate a hardware security key.
 */

import type { Page } from '@playwright/test';
import { createApi } from './api.js';
import { expect, generateUUID, test } from './baseFixtures.js';
import { logoutUrl } from './defaults.js';
import { navigate } from './helpers.js';
import { doLogin } from './login.js';

// Attach a virtual authenticator to the provided page
const addVirtualAuthenticator = async (page: Page) => {
  const client = await page.context().newCDPSession(page);
  await client.send('WebAuthn.enable');
  await client.send('WebAuthn.addVirtualAuthenticator', {
    options: {
      protocol: 'ctap2',
      transport: 'internal',
      hasResidentKey: true,
      hasUserVerification: true,
      isUserVerified: true,
      automaticPresenceSimulation: true
    }
  });
  return client;
};

// Create a new user account (with a known password) for this test
const createUser = async (username: string, password: string) => {
  const api = await createApi({});
  const response = await api.post('user/', {
    data: {
      username: username,
      email: `${username}@example.org`,
      first_name: 'Web',
      last_name: 'Authn'
    }
  });
  expect(response.status()).toBe(201);
  const user = await response.json();

  const pwd = await api.put(`user/${user.pk}/set-password/`, {
    data: { password: password, override_warning: true }
  });
  expect([200, 201]).toContain(pwd.status());

  return user.pk;
};

// Handle a re-authentication prompt (if displayed)
const reauthenticate = async (page: Page, password: string) => {
  const field = page.getByLabel('text-field-password');
  const visible = await field
    .waitFor({ timeout: 3000 })
    .then(() => true)
    .catch(() => false);

  if (visible) {
    await field.fill(password);
    await page.getByRole('button', { name: 'Submit' }).click();
  }
};

test('Login - MFA - WebAuthn', async ({ page, browserName }) => {
  // The virtual authenticator requires the Chrome DevTools Protocol
  test.skip(
    browserName !== 'chromium',
    'WebAuthn virtual authenticator is only available in Chromium'
  );

  const username = `pw-webauthn-${generateUUID().slice(0, 6)}`;
  const password = `Pw-${generateUUID()}`;
  const userId = await createUser(username, password);

  try {
    await addVirtualAuthenticator(page);
    await doLogin(page, { username, password });

    await navigate(page, 'settings/user/security', {
      waitUntil: 'networkidle'
    });

    // Remove the (unverified) email address for this user
    // Note: allauth prevents adding MFA factors while an unverified email exists
    await page.getByLabel(`${username}@example.org`).click();
    await page.getByRole('button', { name: 'Remove' }).click();
    await page
      .getByText('Currently no email addresses are registered')
      .waitFor();

    // Register a new WebAuthn credential
    await page
      .getByRole('button', { name: 'Multi-Factor Authentication' })
      .click();
    await page.getByRole('button', { name: 'add-factor-webauthn' }).click();
    await reauthenticate(page, password);
    await page
      .getByText('WebAuthn credential registered successfully')
      .waitFor();

    // Log out, and log back in using the security key
    await navigate(page, logoutUrl);
    await page.waitForURL('**/web/login');
    await page.getByRole('textbox', { name: 'login-username' }).fill(username);
    await page.getByRole('textbox', { name: 'login-password' }).fill(password);
    await page.getByRole('button', { name: 'Log in' }).click();

    // The MFA page should automatically use the virtual authenticator,
    // and complete the login process
    await page.waitForURL('**/web/mfa');
    await page.waitForURL(/\/web(\/home)?$/, { timeout: 30000 });
    await page.getByRole('button', { name: 'navigation-menu' }).waitFor();

    // Remove the WebAuthn credential
    await navigate(page, 'settings/user/security', {
      waitUntil: 'networkidle'
    });
    await page
      .getByRole('button', { name: 'Multi-Factor Authentication' })
      .click();
    await page.getByRole('button', { name: 'remove-webauthn' }).click();
    await page.getByText('Remove WebAuthn Credential').waitFor();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();
    await reauthenticate(page, password);
    await page.getByText('WebAuthn credential removed successfully').waitFor();
  } finally {
    const api = await createApi({});
    await api.delete(`user/${userId}/`);
  }
});
